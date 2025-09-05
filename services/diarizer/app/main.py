import logging
import os
import tempfile
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Diarizer Service", version="0.2.0")


@app.on_event("startup")
def load_pipeline() -> None:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token:
        logger.warning(
            "No HuggingFace token found, pipeline will be loaded on first request"
        )
        app.state.pipeline = None
        return

    try:
        from pyannote.audio import Pipeline  # type: ignore

        logger.info("Loading pyannote speaker diarization pipeline...")

        # Essai avec modèle le plus récent
        try:
            app.state.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=token,
            )
            logger.info("Successfully loaded pyannote/speaker-diarization-3.1")
        except Exception as e:  # pragma: no cover
            logger.warning(f"Failed to load 3.1 model: {e}")
            # Fallback vers ancienne signature si nécessaire
            try:
                app.state.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=token,
                )
                logger.info(
                    "Successfully loaded pyannote/speaker-diarization-3.1 (legacy API)"
                )
            except Exception as e2:
                logger.warning(f"Failed to load 3.1 model with legacy API: {e2}")
                # Dernier fallback vers modèle 3.0
                app.state.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization",
                    token=token,
                )
                logger.info(
                    "Successfully loaded pyannote/speaker-diarization (fallback)"
                )

        # Option: forcer GPU si demandé
        device = os.getenv("PYANNOTE_DEVICE")
        if device:
            try:
                import torch  # type: ignore

                app.state.pipeline.to(torch.device(device))
                logger.info(f"Pipeline moved to device: {device}")
            except Exception as e:
                logger.warning(f"Failed to move pipeline to device {device}: {e}")
    except Exception as exc:  # pragma: no cover
        app.state.pipeline = None
        logger.error(f"Failed loading pyannote pipeline: {exc}")


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
    logger.info(f"Received diarization request for file: {file.filename}")

    if getattr(app.state, "pipeline", None) is None:
        # Lazy-load to avoid race conditions between /healthz and
        # the first /diarize call
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if token:
            try:
                from pyannote.audio import Pipeline  # type: ignore

                logger.info("Performing lazy load of diarization pipeline...")

                try:
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=token,
                    )
                    logger.info("Lazy loaded pyannote/speaker-diarization-3.1")
                except Exception as e:
                    logger.warning(f"Lazy load failed for 3.1 model: {e}")
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=token,
                    )
                    logger.info(
                        "Lazy loaded pyannote/speaker-diarization-3.1 (legacy API)"
                    )

                setattr(app.state, "pipeline", pipeline)
            except Exception as e:
                logger.error(f"Lazy load failed: {e}")
                pass

    if getattr(app.state, "pipeline", None) is None:
        logger.error("Pipeline not available for diarization")
        raise HTTPException(
            status_code=500, detail="HF_TOKEN not set or pipeline not available"
        )

    tmp_path = None
    try:
        # Sauvegarde temporaire du fichier audio
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = file.file.read()
            tmp.write(content)
            tmp_path = tmp.name
            logger.info(f"Saved {len(content)} bytes to temporary file: {tmp_path}")

        # Exécution de la diarization
        logger.info("Starting diarization process...")
        diarization = app.state.pipeline(tmp_path)  # type: ignore[attr-defined]

        # Traitement des résultats
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

        logger.info(f"Diarization completed: found {len(segments)} segments")
        return JSONResponse({"segments": segments})

    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Diarization failed: {str(e)}")

    finally:
        # Nettoyage du fichier temporaire
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug(f"Cleaned up temporary file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file {tmp_path}: {e}")
