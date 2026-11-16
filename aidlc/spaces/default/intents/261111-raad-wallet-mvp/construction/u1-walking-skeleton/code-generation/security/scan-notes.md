# Local secret scan evidence

Gitleaks v8.24.2 official container, pinned digest b5918eb91b8d2473cec722f066abb4352e4ffdc4ec9f4283ec143aba9ec9ebc4. Scans run offline against read-only working trees with full redaction. Reports contain redacted findings; only file/rule/count metadata is surfaced in conversation. These reports are generated verification evidence, not application source or an assertion that all findings are true secrets.

## Results and bounded triage

- Raad: raw dir scan exit1,355 generic-api-key findings,93.44MB scanned.354 findings are generated cdk.out vendored SDK example/cryptography/PyJWT files; one is the authored U2 security-requirements.md line34.
- Service: raw dir scan exit1,235 generic-api-key findings,28.35MB scanned. All findings are generated cdk.out vendored SDK/examples/cryptography/PyJWT files.
- Parent inspected only the single authored-document line: NFR11.3 prose about immutable Directory versions and replay, containing no credential/token/key value. It is a false positive; U2 was not edited. No broad exclusion or ignore rule was added.
- No application credential was found in the scanned working trees based on report metadata and that bounded document inspection. This is a qualified triage result, not a clean raw scan, a history scan, an executed GitHub check or proof against every possible secret.
- `raad.json` and `service.json` preserve the fully redacted raw findings. All repository mounts were read-only; the separate report directory was writable only for generated evidence. Container network was disabled during scans. The reported image version is pinned, not claimed to be the latest release.
