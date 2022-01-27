from tempfile import TemporaryDirectory
from typing import Type

import joblib
from sklearn.model_selection import cross_val_predict
import wandb
import hydra

from src.models.evaluation import RegressionEvaluation
from src.models import models
from src.utils import read_dataframe_artifact, log_dir, log_file
from src.logger import logger

TARGET_COLUMN = "median_house_price"


def train_evaluate(
    pipeline_class: Type[models.BasePipeline],
    config: dict,
):
    run = wandb.init(
        project=config["main"]["project_name"],
        job_type="cross_validation",
        group=config["main"]["experiment_name"],
    )
    logger.info("Load data fro training model.")
    train_data_name = config["artifacts"]["train_validate_data"]["name"]
    train_data_version = config["artifacts"]["train_validate_data"]["version"]
    df = read_dataframe_artifact(run, f"{train_data_name}:{train_data_version}")

    logger.info("Initialize ml pipeline object.")
    pipeline = pipeline_class.get_pipeline(**(config["model"]["params"]))

    logger.info("predict on hold out data using cross validation.")
    predictions = cross_val_predict(
        estimator=pipeline,
        X=df,
        y=df[TARGET_COLUMN],
        cv=config["evaluation"]["cross_validation_folds"],
        verbose=3,
    )

    model_evaluation = RegressionEvaluation(
        y_true=df[TARGET_COLUMN],
        y_pred=predictions,
    )

    logger.info("train on model on all artifacts")
    pipeline.fit(df, df[TARGET_COLUMN])

    logger.info("Logging performance metrics.")
    run.summary.update(model_evaluation.get_metrics())

    wandb.log(model_evaluation.get_metrics())

    logger.info("Logging model evaluation artifacts.")
    with TemporaryDirectory() as tmpdirname:
        model_evaluation.save_evaluation_artifacts(outdir=tmpdirname)
        log_dir(
            run=run,
            dir_path=tmpdirname,
            type=config["artifacts"]["evaluation"]["type"],
            name=config["artifacts"]["evaluation"]["name"],
            descr=config["artifacts"]["evaluation"]["description"]
        )

    logger.info("Logging model trained on all artifacts as an artifact.")
    with TemporaryDirectory() as tmpdirname:
        file_name = tmpdirname + "model.pickle"
        joblib.dump(pipeline, file_name)
        log_file(
           run=run,
           file_path=file_name,
            type=config["artifacts"]["model"]["type"],
            name=config["artifacts"]["model"]["name"],
            descr=config["artifacts"]["model"]["description"]
        )


@hydra.main(config_path="../../conf", config_name="config")
def main(config):
    model_class = getattr(models, config["model"]["model_class"])
    train_evaluate(
        pipeline_class=model_class,
        config=config,
    )


if __name__ == '__main__':
    main()