import os

import backoff
import requests

from mc_bench.util.logging import get_logger

logger = get_logger(__name__)


class Client:
    def __init__(self, token):
        self.token = token
        self.base_url = os.environ["ADMIN_API_URL"]

    def _make_path(self, path):
        path = path.lstrip("/")
        host = self.base_url.rstrip("/")
        return f"{host}/{path}"

    def _make_request(self, method, path, **kwargs):
        headers = {"Authorization": f"Bearer {self.token}"}

        return requests.request(
            method, self._make_path(path), headers=headers, **kwargs
        )

    def post(self, path, **kwargs):
        return self._make_request("POST", path, **kwargs)

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        logger=logger,
        max_time=30,
        raise_on_giveup=False,
    )
    def update_stage_progress(self, run_external_id, stage, progress, note):
        response = self.post(
            f"/api/run/{run_external_id}/task/progress",
            json={
                "stage": stage,
                "progress": progress,
                "note": note,
            },
        )
        response.raise_for_status()

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        logger=logger,
        max_time=120,
        raise_on_giveup=True,
    )
    def start_run_over(self, run_external_id):
        response = self.post(
            f"/api/run/{run_external_id}/task-retry",
            json={"tasks": ["PROMPT_EXECUTION"]},
        )
        if not response.ok:
            logger.error(
                f"Failed to start run over for run {run_external_id}",
                error=response.text,
            )
        response.raise_for_status()
