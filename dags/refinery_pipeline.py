from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

RUN = "cd /opt/airflow/scripts && python"

with DAG(
    dag_id="training_data_refinery",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["data-refinery"],
) as dag:

    download = BashOperator(task_id="download", bash_command=f"{RUN} download.py")
    clean = BashOperator(task_id="clean", bash_command=f"{RUN} clean.py")
    dedup = BashOperator(task_id="dedup", bash_command=f"{RUN} dedup.py")
    score = BashOperator(task_id="score", bash_command=f"{RUN} quality_score.py")
    shards = BashOperator(task_id="shards", bash_command=f"{RUN} make_shards.py")
    anomalies = BashOperator(task_id="anomalies", bash_command=f"{RUN} shard_anomalies.py")

    download >> clean >> dedup >> score >> shards >> anomalies
