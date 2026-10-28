"""Automatic quality checks run on every take before it is submitted.

Targets follow common speech-corpus practice:
  peak between -30 and -1 dBFS, no clipping, SNR >= 25 dB (ASR) / >= 35 dB (TTS),
  0.2-3 s of silence before and after speech, 1-30 s total length.
"""

import numpy as np

FRAME_SEC = 0.03
CLIP_LEVEL = 0.999

OK, WARN, FAIL = "ok", "warn", "fail"


def _db(x):
    return 20 * np.log10(np.maximum(x, 1e-10))


def analyze(data: np.ndarray, sample_rate: int) -> dict:
    mono = data.mean(axis=1) if data.ndim == 2 else data
    n = len(mono)
    duration = n / sample_rate
    result = {"duration_sec": round(duration, 3), "issues": []}
    if n < sample_rate * 0.1:
        result.update(peak_dbfs=-120.0, noise_floor_dbfs=-120.0, speech_level_dbfs=-120.0,
                      snr_db=0.0, clipped_samples=0, lead_silence_sec=0.0,
                      trail_silence_sec=0.0)
        result["issues"].append((FAIL, "Recording is empty or too short."))
        result["status"] = FAIL
        return result

    peak = float(np.max(np.abs(data)))
    clipped = int(np.sum(np.abs(data) >= CLIP_LEVEL))

    frame = max(1, int(FRAME_SEC * sample_rate))
    frames = mono[: (n // frame) * frame].reshape(-1, frame)
    rms_db = _db(np.sqrt(np.mean(frames ** 2, axis=1)))
    noise_floor = float(np.percentile(rms_db, 10))
    speech_level = float(np.percentile(rms_db, 95))
    snr = speech_level - noise_floor

    # Voice activity: frames clearly above the noise floor.
    threshold = max(noise_floor + 12, -50)
    active = np.where(rms_db > threshold)[0]
    if len(active):
        lead = active[0] * frame / sample_rate
        trail = duration - (active[-1] + 1) * frame / sample_rate
    else:
        lead, trail = duration, 0.0

    result.update(peak_dbfs=round(float(_db(peak)), 1), noise_floor_dbfs=round(noise_floor, 1),
                  speech_level_dbfs=round(speech_level, 1), snr_db=round(snr, 1),
                  clipped_samples=clipped, lead_silence_sec=round(lead, 2),
                  trail_silence_sec=round(max(trail, 0.0), 2))

    issues = result["issues"]
    if not len(active) or snr < 10:
        issues.append((FAIL, "No clear speech detected - check the microphone."))
    if clipped > 0.0005 * n or clipped > 50:
        issues.append((FAIL, f"Clipping detected ({clipped} samples) - speak softer or "
                             "move the mic away."))
    elif result["peak_dbfs"] > -1:
        issues.append((WARN, "Very loud - close to clipping."))
    if result["peak_dbfs"] < -30:
        issues.append((FAIL, "Too quiet - speak louder or move closer to the mic."))
    elif result["peak_dbfs"] < -20:
        issues.append((WARN, "A bit quiet - try speaking a little louder."))
    if len(active) and 10 <= snr < 25:
        issues.append((WARN, f"Background noise is high (SNR {snr:.0f} dB). "
                             "Aim for 25 dB+ (35 dB+ for TTS)."))
    if result["noise_floor_dbfs"] > -45:
        issues.append((WARN, "Noisy background - find a quieter place."))
    if duration < 1.0:
        issues.append((FAIL, "Too short (under 1 second)."))
    elif duration > 30:
        issues.append((WARN, "Longer than 30 s - long clips are harder to use for training."))
    if len(active) and lead < 0.2:
        issues.append((WARN, "Speech starts immediately - wait half a second after "
                             "pressing Start."))
    if len(active) and trail < 0.2:
        issues.append((WARN, "Speech may be cut off at the end - pause before pressing Stop."))
    if lead > 3:
        issues.append((WARN, f"Long silence at the start ({lead:.1f} s)."))
    if trail > 3:
        issues.append((WARN, f"Long silence at the end ({trail:.1f} s)."))

    levels = {lvl for lvl, _ in issues}
    result["status"] = FAIL if FAIL in levels else WARN if WARN in levels else OK
    return result
