from datetime import datetime
from typing import Tuple

import wandb
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import config
from src.logger import logger
from src.utils import read_dataframe_artifact, log_dataframe


def train_validate_split(
    df: pd.DataFrame, validation_ratio: float
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits dataframe into training artifacts and a validation set
    """
    return train_test_split(df, test_size=validation_ratio)


if __name__ == '__main__':
    run = wandb.init(project=config.WANDB_PROJECT, job_type="data_segregation")

    df = read_dataframe_artifact(run, "modelling-artifacts:latest")

    logger.info(f"Split artifacts in train/validate and test artifacts.")
    train_df, validate_df = train_validate_split(
        df,
        config.VALIDATION_SET_RATIO,
    )

    log_dataframe(
        run=run,
        df=train_df,
        type="train-validate-artifacts",
        name="train-validate-artifacts",
        descr="Data for training and validation.",
    )
    log_dataframe(
        run=run,
        df=validate_df,
        type="test-artifacts",
        name="test-artifacts",
        descr="Data for testing.",
    )
