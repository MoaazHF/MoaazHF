<div align="center">
  <img src="./assets/moaaz-banner.svg" alt="Moaaz — Software Engineer" width="100%"/>
</div>

<br/>

I'm a Full Stack Developer working as a contractor at **[RobinFood](https://robinfood.app/)**, a food delivery
platform in Saudi Arabia (think HungerStation / Keeta / Talabat), reporting directly to the CEO. I also study
Computer Science at Capital University (Helwan) — second year, class of 2028.

I don't fill this section with buzzwords. Below is what I've actually shipped, tested, and broken.

---

### What I've actually built at RobinFood

- **Query optimization** — took an admin portal query in TypeORM from ~3 minutes down to ~3 seconds by fixing how it was structured, not just adding an index.
- **Thermal receipt / invoice redesign** — rebuilt PDF generation (PDFKit) for RobinFood's 58mm/203dpi thermal printers used across restaurant partners (AlBaik, Kudo, Deyafa Al-Jawi, and others). This meant solving real, unglamorous problems:
  - Arabic + English mixed text was breaking Arabic letter joining when switching fonts mid-string, so I moved to a single multi-script font with proper reshaping (`arabic-reshaper`) and bidi reordering instead of font-switching.
  - Diagnosed a print-quality bug that turned out to be a DPI/printable-width mismatch, not a font issue.
  - Refactored a single bloated `invoice.service.ts` into focused pieces — `PrinterProfile`, `FontManager`, `LogoManager`, `BidiTextRenderer`, `InvoiceViewModelMapper`, `ReceiptLayoutBuilder` — with a thin orchestrator and OpenTelemetry trace spans for observability.
  - Designed a two-tier logo caching strategy (Redis at startup → in-process memory) so the shared receipt logo isn't reloaded per print.
- **Bug fixes across the stack** — nullable `productOptionCategories` in GraphQL, working-hours sorting, a rush-hour delivery-margin bug in `getNearbyStoresV3`, a TypeORM `IsNull()` bug in `MediaService`.
- **QA across the org** — structured bug documentation (Obsidian-formatted) across the Admin Portal, Partner Portal, and Transactions modules.

---

### Automated Testing

I built a Postman/Newman CLI test suite for RobinFood's **Flash Sale** feature — a two-user flow where one user
(the host) pays to open a shared discount and a second user (the guest) joins to claim it. That kind of flow
can't be tested with single-request scripts, so the suite:

- Runs the full host-pays → guest-joins sequence end-to-end via the Newman CLI (CI-friendly, no manual clicking through the UI every time).
- Hits the **HyperPay/OPPWA** payment sandbox in `INTEGRATOR_TEST` mode with a saved test card registration, instead of mocking payment responses.
- Chains state between requests (payment result → GraphQL token extraction via a Postman post-response script → the guest's join request), which is where most of the actual debugging happened.

I've also explored Playwright and Maestro for E2E coverage on the web and Flutter sides respectively, but the
Newman suite is the one that's actually running.

---

### AWS

Going through NTT's AWS Academy program (Cloud Foundations → Solutions Architect Associate track), on weekends,
specifically to backstop the infrastructure side of the RobinFood backend rather than as a resume line:

- Comfortable with **EC2, IAM, S3** fundamentals; did an IAM policy review for EC2/S3 access at work.
- Completed a guided lab on hybrid storage — **AWS Storage Gateway (S3 File Gateway)** with an NFS share, cross-Region replication, and S3 lifecycle policies.
- Working through the Cloud Architecting curriculum: storage/compute/database layers, networking, securing access, elasticity & monitoring, decoupled and microservice/serverless architectures.
- Actively connecting this to real decisions — e.g. evaluating whether RobinFood's current hosting setup is worth moving, not studying AWS in a vacuum.

---

### Stack I actually use day to day

**Backend** — NestJS · GraphQL/Apollo · TypeORM · PostgreSQL · Redis · RabbitMQ · BullMQ · JWT · Jest/Supertest

**Frontend** — React · TypeScript · Next.js · TailwindCSS

**Mobile** — Flutter (two RobinFood apps: `CustomerAppFlutter`, `DriverAppFlutter`)

**Infra / Ops** — Docker & Docker Compose · AWS (EC2, IAM, S3, Storage Gateway) · OpenTelemetry · Sentry · Firebase Admin · Twilio

**Testing** — Postman/Newman CLI automation · Jest · exploring Playwright & Maestro

---

### Certifications & Training

| Program | Track | Hours |
|---|---|---|
| NTT AWS Academy | Cloud Foundations + Solutions Architect Associate | ongoing |
| DEPI | React Web Development | 159 hrs |
| ITI | Web Development | 120 hrs |
| Capital University (Helwan) | B.Sc. Computer Science, expected 2028 | — |

---

### Outside of RobinFood

Some of what I build to actually learn rather than to ship:

- **Route d'Egypte** — React + Vite tourism site, later migrated to Supabase, deployed on Vercel. Chased down Lighthouse performance issues instead of ignoring them.
- **Subscription Box Portal** — university project, PHP native MVC. I was technical lead for a 6-person team, coordinating three pairs of students.
- **Spin Wheel Eid app** — Flutter + GetX, with weighted prize logic and EmailJS — small, but it's where I actually learned Flutter state management.
- A hotel-management side project I built deliberately to mirror RobinFood's delivery domain patterns, as a way to practice architecture decisions without the production stakes.

My workflow leans heavily on writing detailed spec prompts for AI coding agents (Codex/Antigravity) rather than
having them write code outright — I'd rather understand the *why* behind an architecture than memorize syntax.

---

### Dev setup

Dell G15 5510 (hybrid Intel/NVIDIA, RTX 3050 Ti) running Ubuntu — which means a fair amount of my "learning" has
been NVIDIA driver conflicts, NTFS partition headaches, and getting the Android emulator to stop crashing. Notes
live in Obsidian.

---

<div align="center">

📫 **MoazHasanFarouk@gmail.com** · [GitHub](https://github.com/MoaazHF) · [LinkedIn](https://linkedin.com/in/moazhasan) · [WhatsApp](https://wa.me/201200063681)

</div>
