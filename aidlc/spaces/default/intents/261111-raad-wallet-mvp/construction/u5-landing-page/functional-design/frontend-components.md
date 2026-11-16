# Frontend Components — U5

## Hierarchy and State

Static document contains SkipToContent, Header/RAAD text, LanguageNavigation, Introduction, DemoNotice and RequestTestAccess. Its only state is the selected ar/en document; it stores no identity, balance, session or transfer. The public contact is abdulaziz.alrubai@outlook.com, supplied by the person. The operational alert email is not the public contact.

## Interactions

Language links work without JavaScript and set document language/direction. The contact action is an accessible mail link plus visible selectable address; it never claims delivery or silently falls back to collecting a form. Arabic text mirrors layout while email remains isolated LTR. All links work by keyboard with visible focus, text scales to 200%, and content reflows at 320dp. A missing logo retains the accessible RAAD text. Product copy and Arabic wording require review before release.

## Integration

Only static HTTPS assets from the page's own distribution are necessary. No C1/C3 calls, auth SDK, wallet cookies or payment fields. U5 smoke tests verify both language documents and contact target in each environment; U3 owns tester app builds. Sources: `functional-spec.md`, `unit-of-work.md`, `unit-of-work-story-map.md`, `requirements.md`, `components.md`, `stories.md`, `contract-summary.md` and the refined accessibility checklist.
