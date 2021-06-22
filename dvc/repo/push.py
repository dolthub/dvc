import os

import doltcli as dolt

from ..utils import glob_targets
from . import locked


@locked
def push(
    self,
    targets=None,
    jobs=None,
    remote=None,
    all_branches=False,
    with_deps=False,
    all_tags=False,
    recursive=False,
    all_commits=False,
    run_cache=False,
    revs=None,
    glob=False,
):
    used_run_cache = self.stage_cache.push(remote) if run_cache else []

    if isinstance(targets, str):
        targets = [targets]

    expanded_targets = glob_targets(targets, glob=glob)

    used = self.used_cache(
        expanded_targets,
        all_branches=all_branches,
        all_tags=all_tags,
        all_commits=all_commits,
        with_deps=with_deps,
        force=True,
        remote=remote,
        jobs=jobs,
        recursive=recursive,
        used_run_cache=used_run_cache,
        revs=revs,
    )

    dolt_pushed = 0
    if expanded_targets is not None:
        remote_conf = None
        for t in expanded_targets:
            if os.path.exists(os.path.join(t, ".dolt")):
                remotes = self.config.get("remote", None)
                if not remotes:
                    break
                remote_conf = remotes.get(remote, None)
                if not remote_conf:
                    break
            db = dolt.Dolt(t)
            remote_url = remote_conf.get("url")

            existing_remotes = db.remote()
            found_remote = False
            for r in existing_remotes:
                if r.name == remote:
                    found_remote = True
                    break
            if not found_remote:
                db.remote(name=remote, url="file://" + remote_url, add=True)

            db.push(remote=remote, set_upstream=True, refspec="master")
            dolt_pushed += 1

    return len(used_run_cache) + self.cloud.push(used, jobs, remote=remote) + dolt_pushed
