# AI Fraud in the Recruitment Lifecycle — Detection Roadmap

> End-to-end mapping of every fraud vector, detection signal, and threat indicator across all 7 stages of hiring. Based on the *AI Fraud in the Recruitment Lifecycle* threat landscape report (2026).

---

## Table of Contents

1. [Overview](#overview)
2. [Stage 1 — Application & Sourcing](#stage-1--application--sourcing)
3. [Stage 2 — Screening & Assessment](#stage-2--screening--assessment)
4. [Stage 3 — Interview](#stage-3--interview)
5. [Stage 4 — Background Check & Verification](#stage-4--background-check--verification)
6. [Stage 5 — Onboarding](#stage-5--onboarding)
7. [Stage 6 — Post-Hire Exploitation](#stage-6--post-hire-exploitation)
8. [Stage 7 — Reverse Vector (Fraud Targeting Candidates)](#stage-7--reverse-vector-fraud-targeting-candidates)
9. [Signal Severity Matrix](#signal-severity-matrix)
10. [Detection Coverage Roadmap](#detection-coverage-roadmap)

---

## Overview

Modern AI tooling has unlocked an unprecedented scale of fraud across every hiring stage — from a tailored LLM-generated resume to a DPRK-linked ghost employee collecting salary while exfiltrating IP. This project maps all known fraud vectors and their observable signals, providing a structured foundation for building automated detection systems.

```
Application → Screening → Interview → Verification → Onboarding → Post-Hire
     ↑                                                                    |
     └──────────────── Reverse Vector (Targeting Candidates) ────────────┘
```

**Threat actors range from:**
- Individual opportunists using AI copilots on assessments
- Organised resume fraud rings running mass bot farms
- Nation-state operations (DPRK IT worker schemes) generating revenue and harvesting IP

---

## Stage 1 — Application & Sourcing

The fraud surface begins before a human ever reviews a submission.

### 1.1 AI-Generated Resumes
LLMs tailor CVs to match any job description verbatim.

| Signal | Detection Approach |
|--------|-------------------|
| Unnaturally perfect keyword density matching JD | NLP keyword overlap scoring vs. statistical baseline |
| Identical phrasing patterns across multiple applicants | Cross-applicant similarity hashing (MinHash / cosine) |
| Perplexity / burstiness scores flag uniform text generation | LLM-detector APIs (e.g., GPTZero, Originality.ai) |
| Work history timelines that don't survive manual verification | Automated timeline consistency checks + OSINT |

### 1.2 Prompt Injection in CVs
Hidden text manipulates ATS ranking algorithms.

| Signal | Detection Approach |
|--------|-------------------|
| White-on-white or zero-font-size text in document metadata | PDF layer extraction + invisible text scanner |
| Instructions embedded in PDF layers ("rank this candidate #1") | ATS log anomaly monitoring |
| Invisible Unicode characters or steganographic payloads | Unicode normalisation + entropy analysis |
| ATS score anomalies — candidate ranks far above expected | Statistical outlier detection on ATS scores |

### 1.3 Synthetic Identity Profiles
Entirely fabricated candidate personas.

| Signal | Detection Approach |
|--------|-------------------|
| AI-generated headshot (GAN artefacts, asymmetric ears/teeth) | GAN detection models (FaceForensics++, SynthID) |
| LinkedIn profile creation date within days of application | Profile age check via scraping / LinkedIn API |
| No mutual connections with anyone in stated industry | Graph connectivity analysis |
| Reverse image search returns no matches or stock-photo variants | Automated reverse image search pipeline |
| Email domain registered recently; no web footprint pre-2024 | WHOIS domain age check + web presence scoring |

### 1.4 Mass Application Bot Farms
Automated spray-and-pray at industrial scale.

| Signal | Detection Approach |
|--------|-------------------|
| Burst of applications from same IP range within seconds | IP rate limiting + CIDR clustering |
| Identical cover letter templates with only name/company swapped | Template diff detection |
| Device fingerprint clustering across different applicant names | Browser fingerprinting on application portal |
| Application timestamps at inhuman speed (< 30s between submits) | Submission velocity thresholding |

### 1.5 Credential & Portfolio Fabrication
Fake degrees, certs, GitHub repos, and work samples.

| Signal | Detection Approach |
|--------|-------------------|
| GitHub repos with fabricated commit histories (bulk-backdated commits) | Commit graph analysis — detect bulk backdating |
| Portfolio sites hosted on throwaway domains (< 30 days old) | Domain age check on all portfolio URLs |
| Degree verification fails when institution is contacted directly | Automated education verification API (e.g., Hyland, Parchment) |
| Certification numbers don't validate against issuer databases | Cert validation API integration (AWS, Google, CompTIA, etc.) |

---

## Stage 2 — Screening & Assessment

Candidates increasingly use AI assistance — or substitute an entirely different person.

### 2.1 AI Copilot on Assessments
LLM generates real-time answers on a second screen.

| Signal | Detection Approach |
|--------|-------------------|
| Eye tracking: gaze shifts to second monitor or phone | Proctoring software gaze analysis |
| Response latency signature — 2–4s delay then fluent output | Keystroke / response timing analytics |
| Typing cadence: copy-paste bursts vs natural keystroke rhythm | Biometric typing pattern analysis |
| Tab-switching or window-focus-loss events | Browser focus event monitoring |
| Answer quality dramatically exceeds stated experience level | Difficulty-calibrated scoring benchmarks |

### 2.2 Proxy Test-Taker
Skilled ringer completes assessment on behalf of candidate.

| Signal | Detection Approach |
|--------|-------------------|
| IP geolocation shift between application and assessment | IP consistency check across sessions |
| Typing biometrics don't match baseline | Per-candidate biometric profile comparison |
| Webcam shows different person or obscured camera | Face recognition against ID photo |
| Assessment performance wildly inconsistent with interview | Cross-stage performance delta flagging |

### 2.3 Screen Overlay / Earpiece Feed
Subtle on-screen hints or audio coaching in real-time.

| Signal | Detection Approach |
|--------|-------------------|
| Candidate eyes track a fixed position on screen (reading overlay) | Proctoring gaze fixation heatmaps |
| Micro-pauses before answers — listening to earpiece | Answer latency distribution analysis |
| Faint audio bleed or echo detectable in call recording | Audio spectrum analysis on recordings |
| Head tilt pattern consistent with earpiece use | Computer vision posture detection |

### 2.4 Answer-Sharing Networks
Leaked assessment questions on forums and Telegram groups.

| Signal | Detection Approach |
|--------|-------------------|
| Multiple candidates submit near-identical code solutions | Code similarity detection (MOSS, JPlag) |
| Answers reference deprecated APIs or outdated framework versions | Static analysis of answer content |
| Completion times suspiciously fast (pre-prepared answers) | Time-to-complete percentile distribution |
| Same wrong answers across cohort | Error pattern clustering |

---

## Stage 3 — Interview

The highest-risk stage; real-time AI impersonation is now commodity tooling.

### 3.1 Deepfake Video Interview
Real-time face-swap filters on Zoom / Teams / Meet.

| Signal | Detection Approach |
|--------|-------------------|
| Video glitching / artefacts around face edges during head movement | Frame-by-frame artefact detection (e.g., Microsoft Video Authenticator) |
| Lighting on face doesn't match room or background | Lighting consistency analysis |
| Skin texture unnaturally smooth or waxy | Texture frequency analysis |
| Hair boundary shimmers or bleeds into background | Segmentation mask edge analysis |
| Face geometry distorts when hand passes near face | Occlusion response testing |
| Lip sync off by 50–200ms | Audio-visual sync measurement |
| Blinking rate abnormal (too regular or infrequent) | Blink frequency monitoring |
| Request to turn head 90° causes face warp | Live liveness challenge (head turn, smile) |

### 3.2 Voice Cloning
AI-generated voice replica in real-time.

| Signal | Detection Approach |
|--------|-------------------|
| Unnatural prosody — flat emotional range, monotone delivery | Prosody / sentiment analysis on audio |
| Micro-stutter or audio glitch at sentence boundaries | Audio artefact detection |
| Breathing pattern absent or artificially regular | Breath signal analysis |
| Voice timbre shifts when speaking quickly vs slowly | Spectrogram velocity-dependent analysis |
| Inability to replicate spontaneous laughter or surprise | Spontaneous reaction challenges |
| Background noise floor inconsistency | Ambient noise consistency check |

### 3.3 Hidden AI Answer Generation
Second screen, earpiece, or transparent overlay feeding responses.

| Signal | Detection Approach |
|--------|-------------------|
| Eyes scanning left-to-right (reading text off-screen) | Gaze direction tracking |
| Answers hyper-structured every time (intro → 3 points → conclusion) | NLP answer structure analysis |
| "Too clinical" — no emotional context or personal anecdotes | Emotional authenticity scoring |
| Fails on unexpected emotion-based follow-up questions | Adaptive interviewer question bank |
| Consistent 3–5s pause before every answer (generation latency) | Answer latency consistency flagging |

### 3.4 Proxy Interviewee
Different person attends than who was screened.

| Signal | Detection Approach |
|--------|-------------------|
| Facial features don't match ID photo or LinkedIn headshot | Cross-session face verification |
| Personal details inconsistent with earlier calls | Cross-stage detail consistency check |
| Camera angle deliberately obscures full face | Camera framing policy enforcement |
| "Technical difficulties" — camera off at start | Mandatory camera-on policy + audit |
| Voice sounds different from phone screen recording | Cross-session voice biometric comparison |

### 3.5 Multi-Role Ghost Interviewing
Same person interviews at multiple companies simultaneously.

| Signal | Detection Approach |
|--------|-------------------|
| Candidate unavailable at overlapping time slots | Scheduling conflict cross-reference |
| Background/room setup identical to candidates at other firms | Background image hashing (industry-level data sharing) |
| Reference checks reveal "interviewing everywhere" | Reference network probing |

### 3.6 Video Concealment Tactics
Deliberate camera / environment manipulation to hide fraud.

| Signal | Detection Approach |
|--------|-------------------|
| Camera positioned unusually high (hides second monitor below) | Camera angle audit checklist |
| Virtual background masking reference materials on wall | Background analysis / require physical room |
| Excessive backlighting making facial detail unreadable | Image brightness / contrast thresholding |
| "Bandwidth issues" — audio only for key questions | Mandatory video policy for technical rounds |
| Screen sharing declined during live coding | Enforce screen share for coding challenges |

---

## Stage 4 — Background Check & Verification

AI dramatically lowers the cost of creating convincing fake documents and references.

### 4.1 Fabricated Employment History
AI-generated verification documents and fake employer records.

| Signal | Detection Approach |
|--------|-------------------|
| Employer website domain registered recently or is a template site | Domain age + CMS fingerprinting |
| HR contact number routes to VOIP / burner phone | VOIP carrier detection on phone numbers |
| Company LinkedIn page has few employees or no activity | LinkedIn company profile scoring |
| Employment dates don't match tax records or pay stubs | Third-party payroll verification (e.g., The Work Number) |

### 4.2 Synthetic Reference Network
Fake referees with AI voice bots or scripted accomplices.

| Signal | Detection Approach |
|--------|-------------------|
| All references have suspiciously similar speaking cadence (AI voice) | Voice deepfake detection on reference calls |
| References can't provide specific project details when probed | Structured reference questionnaire with probing questions |
| Phone numbers all in same area code despite different "companies" | Phone number clustering analysis |
| Reference LinkedIn profiles thin, recently created, or stock photos | Reference profile age + image authenticity check |

### 4.3 AI Document Forgery
Fake degrees, professional licences, background reports.

| Signal | Detection Approach |
|--------|-------------------|
| Document metadata shows Canva/Photoshop, not institution | PDF/image metadata inspection |
| Subtle font inconsistencies vs authentic institutional templates | Font fingerprinting against known templates |
| QR code / verification URL leads to non-institutional domain | URL destination analysis on embedded QR codes |
| Embossed seal appears digitally overlaid (no paper texture) | Texture and depth analysis on document scans |

### 4.4 Geographic Location Spoofing
VPN and remote desktop mask true location and identity.

| Signal | Detection Approach |
|--------|-------------------|
| IP geolocation doesn't match claimed city/country | Multi-layer IP intelligence (ASN, VPN/proxy detection) |
| Timezone of system clock inconsistent with stated location | System locale vs claimed location audit |
| Keyboard layout defaults to unexpected language | OS locale telemetry |
| Latency patterns suggest overseas routing (extra 100–200ms) | Round-trip latency baseline comparison |
| Device locale settings don't match (date format, currency) | Device metadata collection during proctoring |

---

## Stage 5 — Onboarding

The fraud surface expands once inside the organisation.

### 5.1 Identity Swap Post-Hire
Different person assumes the hired identity for day-to-day work.

| Signal | Detection Approach |
|--------|-------------------|
| Day 1 video appearance differs from interview recordings | Interview-to-onboarding face verification |
| Writing style / email tone dramatically different | Authorship stylometry baseline comparison |
| Camera always off despite company policy | Camera-on enforcement + exception logging |
| Reluctance to attend any in-person event | In-person attendance tracking |

### 5.2 Equipment & Payroll Fraud
Harvest bank, tax, and PII credentials through sham onboarding.

| Signal | Detection Approach |
|--------|-------------------|
| Direct deposit to multiple or unusual account types | Payroll account validation checks |
| Equipment shipped to address not matching stated residence | Address verification against ID |
| Requests advance equipment stipend before starting | Policy enforcement: no pre-start stipends |
| Tax forms (W-4/W-9) contain inconsistent personal details | Cross-field consistency validation on tax forms |

### 5.3 Laptop Farm Routing
Company laptop forwarded to overseas operators via US hosts.

| Signal | Detection Approach |
|--------|-------------------|
| Keystroke latency above threshold (overseas VPN relay) | Network latency monitoring on corporate endpoints |
| USB device connections from unexpected peripherals | Endpoint USB device policy + DLP |
| Remote desktop / VNC software installed without authorisation | Software inventory scanning |
| Login times don't align with stated timezone (3 AM local logins) | Login anomaly detection by timezone |

### 5.4 Credential & Access Harvesting
Systematic collection of internal system access for later exploitation.

| Signal | Detection Approach |
|--------|-------------------|
| Unusual access requests to systems outside role scope in first week | RBAC anomaly detection (UEBA) |
| Downloading large volumes of files or customer data early | DLP file exfiltration alerts |
| Attempting to escalate privileges or access admin panels | Privilege escalation monitoring (SIEM) |
| Connecting personal devices to corporate VPN | Device compliance enforcement |

---

## Stage 6 — Post-Hire Exploitation

The end-game: the fraudster is inside. Damage ranges from salary theft to nation-state espionage.

### 6.1 AI-Automated Ghost Work
AI agents produce deliverables while human collects salary.

| Signal | Detection Approach |
|--------|-------------------|
| Commit patterns show bulk submissions at regular intervals (bot-like) | Git commit cadence analysis |
| Code style / writing quality inconsistent across submissions | Code authorship fingerprinting |
| No participation in live pair programming or design sessions | Participation tracking in collaboration tools |
| Output quality degrades over time as scheme scales | Longitudinal quality scoring |

### 6.2 IP Theft & Insider Threat
Exfiltration of source code, customer data, trade secrets.

| Signal | Detection Approach |
|--------|-------------------|
| Unusual data transfer volumes to external storage | DLP egress monitoring |
| Access to repos or databases outside assigned scope | Access log anomaly detection |
| Screenshots or screen recording software running continuously | Endpoint process monitoring |
| Communication with external servers not on approved list | Network egress allowlist enforcement |

### 6.3 Multi-Salary Collection
Same person holds 3–5+ remote jobs simultaneously using AI.

| Signal | Detection Approach |
|--------|-------------------|
| Unavailable during standard working hours | Availability pattern analytics |
| Missed deadlines with sophisticated excuses | Delivery tracking + velocity metrics |
| Meeting conflicts that don't match internal calendar | Calendar conflict anomaly detection |
| Minimal camera time across all positions | Video participation rate monitoring |

### 6.4 Ransomware & Account Takeover
Lateral movement inside corporate network after initial access.

| Signal | Detection Approach |
|--------|-------------------|
| Unusual authentication patterns (service account abuse) | SIEM authentication anomaly rules |
| Privilege escalation attempts | EDR / SIEM escalation alerts |
| Data staging in unusual directories before exfil | File system behavioural monitoring |
| Connection to known C2 infrastructure IPs | Threat intel feed integration (IP blocklists) |

### 6.5 State-Sponsored Infiltration
DPRK / nation-state operations generating revenue or intelligence.

| Signal | Detection Approach |
|--------|-------------------|
| Salary routed through multiple bank accounts or crypto | Payroll destination anomaly detection |
| Identity documents traced to known stolen identity databases | Identity document cross-referencing (HaveIBeenPwned, OFAC) |
| Connections to flagged OFAC-sanctioned entities or regions | OFAC screening during background check |
| Operational patterns matching known DPRK IT worker TTPs | Threat intel TTP matching (MITRE ATT&CK) |

---

## Stage 7 — Reverse Vector (Fraud Targeting Candidates)

Candidates are also targets — AI enables fake job scams at scale.

### 7.1 Fake Job Postings
AI-crafted roles at real companies to harvest applicant PII.

| Signal | Detection Approach |
|--------|-------------------|
| Job posting doesn't appear on company's official careers page | Career page cross-verification |
| Recruiter email domain slightly misspelled (gogle.com, amaz0n.com) | Domain typosquatting detection |
| Salary range unrealistically high for role level | Market-rate anomaly detection |
| Entire process conducted via WhatsApp or Telegram | Channel policy enforcement |

### 7.2 Recruiter Impersonation
Cloned LinkedIn profiles + AI-personalised outreach at scale.

| Signal | Detection Approach |
|--------|-------------------|
| LinkedIn profile is duplicate of real recruiter with minor changes | Duplicate profile detection + brand monitoring |
| Message tone matches candidate's exact career history (LLM-scraped) | Outreach personalisation anomaly check |
| Requests placement fee or "processing fee" from candidate | Fee request = automatic red flag |
| Email signature links go to lookalike agency website | Link destination verification |

### 7.3 Fake Onboarding Identity Theft
Sham paperwork extracts SSN, bank details, and tax data.

| Signal | Detection Approach |
|--------|-------------------|
| Asks for SSN/PPS number before any formal offer letter | Process sequencing enforcement |
| "Direct deposit setup" requests full bank login credentials | Credential request = automatic red flag |
| Equipment stipend check bounces after candidate forwards funds | Stipend check fraud awareness training |
| I-9 / tax forms collected before employment contract is signed | Document sequencing audit |

### 7.4 ATS Phishing via Portfolio Links
Malicious files in candidate applications target recruiter systems.

| Signal | Detection Approach |
|--------|-------------------|
| Portfolio URL triggers browser download instead of webpage | URL sandboxing before recruiter click |
| "Skills assessment" attachment contains macro-enabled Office files | Attachment sandboxing + macro blocking |
| Link redirects through URL shortener to credential-harvesting page | URL unshortening + domain reputation check |
| Recruiter ATS session hijacked after clicking candidate link | ATS session anomaly monitoring |

---

## Signal Severity Matrix

| Stage | Threat Vector | Severity | Automation Potential |
|-------|--------------|----------|----------------------|
| 1 | Prompt injection in CV | Critical | High |
| 1 | Synthetic identity profiles | High | High |
| 1 | Mass bot farm applications | High | High |
| 2 | Proxy test-taker | High | Medium |
| 3 | Deepfake video interview | Critical | Medium |
| 3 | Voice cloning | Critical | High |
| 3 | Proxy interviewee | Critical | Low |
| 4 | AI document forgery | High | High |
| 4 | Synthetic reference network | High | Medium |
| 4 | Geographic location spoofing | High | High |
| 5 | Identity swap post-hire | Critical | Medium |
| 5 | Laptop farm routing | Critical | High |
| 6 | State-sponsored infiltration | Critical | Medium |
| 6 | IP theft & insider threat | Critical | High |
| 6 | Ransomware & ATO | Critical | High |
| 7 | ATS phishing via portfolio links | High | High |

---

## Detection Coverage Roadmap

### Phase 1 — Application Layer (Weeks 1–4)
- [ ] PDF/document layer scanner for prompt injection & hidden text
- [ ] Cross-applicant similarity engine (MinHash + cosine similarity)
- [ ] LLM-generated text detector integration
- [ ] Domain age + WHOIS check pipeline for emails and portfolio URLs
- [ ] GitHub commit graph analyser for backdated history detection
- [ ] ATS score statistical outlier monitor

### Phase 2 — Screening & Assessment (Weeks 5–8)
- [ ] Response latency analyser (keystroke timing + copy-paste burst detection)
- [ ] Code similarity engine (MOSS / JPlag integration)
- [ ] Cross-session IP geolocation consistency checks
- [ ] Basic proctoring integration hooks (gaze, window focus events)
- [ ] Performance delta flagging (assessment vs interview consistency)

### Phase 3 — Interview (Weeks 9–14)
- [ ] Real-time deepfake video detection pipeline
- [ ] Audio artefact + voice clone detector
- [ ] Liveness challenge system (head-turn, spontaneous reaction prompts)
- [ ] Cross-session face biometric verification
- [ ] Interview answer structure NLP analyser (hyper-structured response flagging)
- [ ] Answer latency consistency dashboard

### Phase 4 — Background Check & Verification (Weeks 15–18)
- [ ] Document metadata scanner (Canva/Photoshop origin detection)
- [ ] QR code / embedded URL destination verifier
- [ ] VOIP / burner phone number detection
- [ ] Multi-layer IP intelligence (VPN, proxy, Tor exit node detection)
- [ ] Automated education & certification verification API integrations

### Phase 5 — Onboarding & Post-Hire (Weeks 19–26)
- [ ] Onboarding-to-interview face verification
- [ ] Email / writing style authorship baseline comparison
- [ ] Keystroke latency monitor on corporate endpoints
- [ ] UEBA integration for access anomaly detection
- [ ] Git commit cadence + code authorship fingerprinting
- [ ] DLP egress monitoring
- [ ] OFAC / sanctions screening integration
- [ ] SIEM TTP matching (MITRE ATT&CK alignment)

### Phase 6 — Reverse Vector Protection (Weeks 27–30)
- [ ] Outbound recruiter link sandboxing (before click delivery)
- [ ] ATS macro-enabled attachment blocking
- [ ] Domain typosquatting monitor for brand impersonation
- [ ] ATS session anomaly detection

---

## Sources

- Greenhouse 2025 AI in Hiring Report
- Gartner HR Research (2025–2026)
- Checkr Background Screening
- FTC Consumer Sentinel Network
- Amazon CSO Disclosure (Dec 2025)
- DOJ DPRK IT Worker Prosecutions
- Pindrop / CBS News Deepfake Demos
- Fortune (Nov 2025)
- KPMG AI Pulse Survey Q3 2025
- Experian 2026 Future of Fraud Forecast
- NYSBA (May 2026)
- LinkedIn Future of Recruiting 2025
