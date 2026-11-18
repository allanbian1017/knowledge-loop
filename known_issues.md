# Known Issues Registry

Reusable environment failures and supported recovery steps. Keep private execution evidence and machine-specific paths outside the public checkout.

- **[Google Workspace authentication]**: Commands report expired/revoked credentials — OAuth authorization is invalid → Use the documented user authentication flow, then verify bounded read access before resuming.
- **[macOS keyring]**: A direct read and a redirected capture can have different authorization outcomes — Host execution permissions may differ → Stop the affected workflow and restore the supported authorization; do not infer that repeated login is always the fix.
- **[Source access]**: Threads login walls or protected websites prevent complete extraction — The documented route lacks required access → Stop and report the missing access rather than bypassing tools or fabricating content.
- **[Browser mode]**: Some native/CDP modes differ across operating systems — Installation alone does not establish mode support → Use only documented, verified macOS modes.
- **[Worker capacity]**: Excessive parallel dispatch can exhaust quotas — Tool/host limits vary → Bound waves to actual available worker capacity and preserve every completion/failure.
- **[Google Tasks update]**: Some update methods require identity in both path parameters and JSON body — API contracts differ by method → Inspect the documented CLI schema before invoking the selected method.
- **[Python testing]**: An optional recording plugin can fail with newer HTTP libraries — The globally installed plugin is incompatible → Run the documented pytest command with `-p no:recording`.
- **[Protected agent directories]**: Sandbox writes can fail despite a writable project root — Directory-specific grants require scoped approval → Stage changes and use the normal approved write mechanism; do not alter protection settings.
- **[Code graph]**: An existing graph directory can have an unreadable database — Index availability is not guaranteed → Report the failure and preserve the index; use source inspection when project rules permit it.
- **[GitHub preflight]**: A connector can return not-found while a local checkout exists — Remote access is not verified by local Git state → Restore authorized repository access before remote operations; do not assume visibility or PR status.
- **[Historical source tests]**: An obsolete session-learning test imports an absent module — Source history contains a removed implementation → Keep this baseline separate from tests of migrated active functionality.
- **[Cross-repository cutover]**: Default-sandbox preflight reports configured output directories are not writable — Directory grants differ by execution context → Normal scoped approval passes preflight and an isolated staging probe; verify unattended host access separately, without changing protection settings or assuming one approval grants future access.
- **[GitHub SSH transport]**: Fetch or push fails with public-key authentication and unavailable interactive askpass — The execution session has no usable SSH identity → Verify the existing GitHub CLI account and use its credential helper for a scoped HTTPS Git invocation, without printing tokens or changing the saved remote.
- **[GitHub PR creation]**: The connected integration can read repository metadata but returns permission denied when creating a pull request — Read access does not establish write capability → Use the separately verified, authorized GitHub CLI account for the requested PR operation; retain the same repository and branch scope.
