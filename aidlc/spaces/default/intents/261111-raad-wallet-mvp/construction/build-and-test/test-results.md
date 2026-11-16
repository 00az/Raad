# U1 Verification Checkpoint

Conversation language: English.

This isolated verification run follows the person's approval of U1 and request to fix AWS and mobile verification. It does not certify later units or advance the main workflow. Sources: `construction/u1-walking-skeleton/code-generation/code-generation-plan.md`, `unit-test-instructions.md`, and `code-summary.md`.

## Current evidence

| Check | Command / location | Result |
|---|---|---|
| AWS authentication | `aws login`, then `aws sts get-caller-identity` | Restored default credentials; account 027863026273 verified. No credentials recorded here. |
| Public ECR authentication | `aws ecr-public get-login-password --region us-east-1` piped directly into Docker login | Login succeeded. Image download completed: sha256:28c6fdd016bb4922d8f89f5e6dc477a31c80e3999cce2222ea22c602930a30f3. Packaging is not yet established; the fixture-input synth request was interrupted by the person. |
| DNS / certificate inventory | Route 53 hosted zones; ACM certificates in us-east-1 | Both empty. No domain or alert email has been supplied. |
| Deployed stacks | CloudFormation list in us-east-1 | No RAAD stacks; unrelated existing stacks were left untouched. |
| Mobile full unit/widget/contract suite | `flutter test --coverage` in registered mobile checkout | 106 passed, exit 0. |
| Mobile coverage | `dart run tool/check_coverage.dart` | 95.11%, 953/1002 measured lines; 80% floor passed, exit 0. |
| Mobile static analysis | `flutter analyze` | No issues, exit 0. |
| iOS contract-fake journey | `flutter test integration_test/walking_skeleton_test.dart -d 37B82BED-B4F1-445F-A9D3-CE8C9415B1BB` | Passed on iPhone 17 Pro simulator, iOS 26.2; one journey plus teardown. Xcode build succeeded. |
| Android contract-fake journey | Same integration file, `-d emulator-5554` | Passed on Pixel 6 API 34 emulator, exit 0; one journey plus teardown. Gradle build and APK installation succeeded. |
| Live public API / iOS / Android journeys | `scripts/verify-dev.sh` | Unverified: no deployed RAAD API, pool/client, runtime fixture secret, or real C4 dev configuration. Existing mobile file is an example only. |

## Limits and next steps

The person supplied `jjii0@hotmail.com` as the operational alert destination and authorized selecting an available domain starting with `api.dev.`. Route 53 Domains reports `raadwallet-demo.com` AVAILABLE with a USD 16 registration price; proposed API hostname is `api.dev.raadwallet-demo.com`. Registration has not been purchased. Purchase approval and real registrant contact details remain prerequisites; the hostname is not owned or live yet.

Superseding cost constraint: the person declined registration and requested a free option with no cost. No domain purchase or paid deployment is authorized. A CloudFront-generated hostname avoids registration and hosted-zone fees, but the backend/WAF/telemetry deployment can still incur AWS charges. Clarification is pending on whether only domain fees or all hosting charges must be avoided. Existing local simulator results remain valid.

The simulator journey above uses the app's existing contract fake. It does not establish Cognito compatibility, AWS persistence, CloudFront origin restrictions, or public latency. No dev test identities, wallets or transfers were created. No deployment or migration ran. No mobile application source was edited.

The person subsequently requested real credentials/configuration. Real AWS authentication is verified for account 027863026273; no AWS key is written into source. Use actual environment inputs for the next synthesis/deployment attempt. Real deployment needs the person's API domain and alert destination, DNS validation, environment outputs and the existing review/deployment process. Never fabricate those values or count an example configuration as deployed evidence.
