import logging
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from config import load_config

logger = logging.getLogger(__name__)




def save_raw(df, name):
    """Save the raw scraped table exactly as extracted, with a timestamp in the file name."""
    raw_dir = Path(load_config()["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = raw_dir / f"{name}_{stamp}.csv"
    df.to_csv(path, index=False)
    logger.info("Saved raw data to %s", path)
    return path

def load_raw(path):
    """Read a saved raw file back in, exactly as it was scraped."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)