import os
import tempfile
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="Diarizer Service", version="0.1.0")


@app.on_event("startup")
def load_pipeline() -> None:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token:
        # On démarre quand même; l'appel renverra une 500 claire
        app.state.pipeline = None
        return
    try:
        from pyannote.audio import Pipeline  # type: ignore

        # Essai 1: signature historique
        try:
            app.state.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        except Exception:  # pragma: no cover
            # Essai 2: certaines versions attendent 'token='
            app.state.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=token,  # type: ignore
            )

        # Option: forcer GPU si demandé
        device = os.getenv("PYANNOTE_DEVICE")
        if device:
            try:
                import torch  # type: ignore

                app.state.pipeline.to(torch.device(device))
            except Exception:
                pass
    except Exception as exc:  # pragma: no cover
        app.state.pipeline = None
        print(f"[startup] Failed loading pyannote pipeline: {exc}")


@app.get("/healthz")
def healthz() -> dict:
    # Lazy load if not yet loaded and token available
    if not getattr(app.state, "pipeline", None):
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if token:
            try:
                from pyannote.audio import Pipeline  # type: ignore

                try:
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=token,
                    )
                except Exception:
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=token,  # type: ignore
                    )
                setattr(app.state, "pipeline", pipeline)
            except Exception as exc:  # pragma: no cover
                print(f"[healthz] Lazy load failed: {exc}")
    return {"status": "ok", "pipeline": bool(getattr(app.state, "pipeline", None))}


@app.post("/load")
def load() -> JSONResponse:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token:
        return JSONResponse(
            {"loaded": False, "error": "Missing HF token"}, status_code=500
        )
    try:
        from pyannote.audio import Pipeline  # type: ignore

        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        except Exception:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=token,  # type: ignore
            )
        device = os.getenv("PYANNOTE_DEVICE")
        if device:
            try:
                import torch  # type: ignore

                pipeline.to(torch.device(device))
            except Exception:
                pass
        setattr(app.state, "pipeline", pipeline)
        return JSONResponse({"loaded": True})
    except Exception as exc:  # pragma: no cover
        return JSONResponse({"loaded": False, "error": str(exc)}, status_code=500)


@app.post("/diarize")
def diarize(file: UploadFile = File(...)) -> JSONResponse:
    if getattr(app.state, "pipeline", None) is None:
        # Lazy-load to avoid race conditions between /healthz and
        # the first /diarize call
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if token:
            try:
                from pyannote.audio import Pipeline  # type: ignore

                try:
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=token,
                    )
                except Exception:
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=token,  # type: ignore
                    )
                setattr(app.state, "pipeline", pipeline)
            except Exception:
                pass
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(
            status_code=500, detail="HF_TOKEN not set or pipeline not available"
        )

    try:
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        diarization = app.state.pipeline(tmp_path)  # type: ignore[attr-defined]
        segments: List[dict] = []
        for speech_turn, _, speaker in diarization.itertracks(yield_label=True):
            start_ms = int(speech_turn.start * 1000)
            end_ms = int(speech_turn.end * 1000)
            segments.append(
                {
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "speaker": str(speaker),
                }
            )
        return JSONResponse({"segments": segments})
    finally:
        try:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
