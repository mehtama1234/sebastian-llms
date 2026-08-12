from __future__ import annotations

from dataclasses import dataclass

from .benchmark_schema import BenchmarkManifest, RealTask


@dataclass(slots=True)
class TaskPack:
    manifest: BenchmarkManifest

    def tasks_for_repo(self, repo_id: str) -> list[RealTask]:
        return [task for task in self.manifest.tasks if task.repo_id == repo_id]

    def tasks_for_class(self, task_class: str) -> list[RealTask]:
        return [task for task in self.manifest.tasks if task.task_class == task_class]

    def tasks_for_difficulty(self, difficulty: str) -> list[RealTask]:
        return [task for task in self.manifest.tasks if task.difficulty == difficulty]

    def long_context_tasks(self) -> list[RealTask]:
        return [task for task in self.manifest.tasks if task.long_context]

    def slice(
        self,
        *,
        repo_id: str | None = None,
        task_class: str | None = None,
        difficulty: str | None = None,
        long_context: bool | None = None,
    ) -> list[RealTask]:
        tasks = self.manifest.tasks
        if repo_id is not None:
            tasks = [task for task in tasks if task.repo_id == repo_id]
        if task_class is not None:
            tasks = [task for task in tasks if task.task_class == task_class]
        if difficulty is not None:
            tasks = [task for task in tasks if task.difficulty == difficulty]
        if long_context is not None:
            tasks = [task for task in tasks if task.long_context is long_context]
        return tasks
