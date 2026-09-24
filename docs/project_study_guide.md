# PCB Inspection System — Study Guide
## Read This to Understand the Full Project & Explain It to Your Team

---

## 1. The One-Line Summary

> **We photograph a circuit board, and our software tells you if any parts are missing or sitting wrong — using just a normal laptop camera.**

That's it. Everything else is how we make that happen reliably and prove it works.

---

## 2. The Real-World Problem We're Solving

In a factory that builds electronics (phones, laptops, routers), **thousands of circuit boards (PCBs)** move down a production line every day. Each board has dozens to hundreds of tiny components soldered onto it — chips, capacitors, resistors, connectors.

**Things that go wrong:**
- A component **doesn't get placed** at all (the pick-and-place machine missed it)
- A component is there but **tilted** or **not fully pushed down** (it's sitting crooked)
- A tiny component **stands up on one end** like a tombstone (called "tombstoning")

**Current solution in factories:** Expensive machines called **AOI (Automated Optical Inspection)** that cost ₹40 lakh to ₹1.5 crore. They use special 3D cameras and projectors.

**Our project:** Do something similar using **just a regular laptop camera** and **AI software** — costing essentially ₹0 in hardware.

---

## 3. How Our System Works — The Simple Version

Think of it like a "Spot the Difference" game:

```
Step 1:  Take a photo of a PERFECT board          → This is our "answer key"
Step 2:  Take a photo of the board we're TESTING   → This is the "student's paper"
Step 3:  Compare them                              → Find the differences
Step 4:  Report what's wrong                       → Grade the board
```

**That's literally the core idea.** Everything else is engineering to make Steps 3 and 4 accurate.

---

## 4. The Physical Setup

```
┌─────────────┐                              ┌─────────────┐
│  LAPTOP A   │         Ubiquiti WiFi         │  LAPTOP B   │
│  (Camera)   │  ───────────────────────────► │  (Brain)    │
│             │       sends the photo         │             │
│  Has webcam │                               │  Runs the   │
│  pointed at │                               │  AI code    │
│  the board  │                               │             │
└─────────────┘                               └─────────────┘
       │                                             │
       ▼                                             ▼
  PCB sits here                               Returns result:
  on the table                                "Board PASS / FAIL"
                                              + annotated image
```

**Why two laptops?**
- Laptop A = the "camera" (in a real factory, this would be a camera on the production line)
- Laptop B = the "brain" (runs all the heavy AI processing)
- They talk over a **Ubiquiti network** (a WiFi router with a fixed IP address)

**Why not just one laptop?**
- In a real factory, the camera is mounted above the conveyor belt (far from the server room)
- We're simulating that real-world separation
- It also shows the judges we understand production architecture

---

## 5. The Two Types of Inspection We Do

### 🔍 Inspection Type 1: "Is the part there?" (2D Detection)

This is classic image comparison:

1. We have a photo of the **perfect board** (golden reference)
2. We have a photo of the **test board**
3. We line them up perfectly (alignment)
4. We compare small regions — one region per component
5. If a region looks **very different** from the reference → that part is probably missing

**The technical terms:**
- **SSIM (Structural Similarity Index)** — a mathematical way to say "how similar do these two image patches look?" Score of 1.0 = identical, score of 0.0 = completely different. If SSIM drops below 0.70 for a component region → we flag it as missing.
- **absdiff** — literally subtract one image from the other, pixel by pixel. Where the difference is big → something changed.

**Analogy:** Like overlaying two transparencies on a light table and looking for spots where they don't match.

---

### 📐 Inspection Type 2: "Is the part sitting correctly?" (3D / Depth Check)

This is the clever part. Even if a component IS present, it might be:
- **Tilted** (one side is higher than the other)
- **Not fully seated** (floating above the board)
- **Tombstoned** (standing up vertically on one end)

A flat 2D photo can't always catch this — the component "looks" present from above but is sitting wrong.

**Our solution: Monocular Depth Estimation**

We use an AI model called **Depth Anything V2** that takes a normal 2D photo and **estimates how far each pixel is from the camera**. It creates a "depth map" — a grayscale image where:
- **Bright = close to camera** (things that stick up)
- **Dark = far from camera** (things that are flat/recessed)

```
Original Photo          →    Depth Map (AI-generated)
┌──────────────┐             ┌──────────────┐
│  [IC] [cap]  │             │  ██░░ ██░░   │  (bright = tall components)
│  [res] [LED] │             │  ░░░░ ░░░░   │  (dark = flat board surface)
└──────────────┘             └──────────────┘
```

**Then we compare depth maps:**
- Golden reference board → reference depth map
- Test board → test depth map
- If a component region's depth is **very different** from the reference → height/tilt anomaly

**Key point:** This AI model is **pretrained** — we don't need to train it ourselves. We just download it and run it. It learned to estimate depth from millions of real-world photos.

**Analogy:** It's like having X-ray vision that tells you "this capacitor is sitting 2mm higher than it should be" — but from a normal photo.

---

## 6. Key Technical Terms — Explained Simply

| Term | What It Means | Analogy |
|---|---|---|
| **PCB** | Printed Circuit Board — the green/blue board with components soldered on | The "motherboard" inside any electronic device |
| **Golden Reference** | The photo of a perfect board with all components correctly placed | The answer key for an exam |
| **ROI (Region of Interest)** | A rectangle drawn around one component on the reference image | Circling a question on the answer key |
| **Homography / Alignment** | Mathematically warping the test photo so it lines up perfectly with the reference | Adjusting a transparency to match another one |
| **ORB Features** | Special "landmark points" the algorithm finds in both images to figure out how to align them | Like matching street corners on two slightly different maps |
| **SSIM** | A score (0 to 1) measuring how similar two image patches are | A similarity percentage — 0.95 = 95% similar |
| **CLAHE** | A technique to fix uneven lighting in photos | Like auto-brightness but smarter |
| **Depth Map** | A grayscale image showing distance-from-camera for each pixel | A topographic map — lighter = higher |
| **Monocular Depth** | Estimating depth from a single camera (mono = one) | Guessing distance with one eye closed |
| **Depth Anything V2** | The specific AI model we use for depth estimation (made by researchers in 2024) | Our "depth vision" AI brain |
| **Health Index** | A single score (0 to 1) summarizing board quality | Like a GPA — one number for overall performance |
| **IPC-A-610** | The global industry standard for inspecting electronic assemblies | Like ISO 9001 but specifically for circuit boards |
| **DPMO** | Defects Per Million Opportunities — a factory quality metric | Like "error rate per million chances" |
| **GR&R** | Gauge Repeatability & Reproducibility — does our system give the same answer each time? | Like checking if a weighing scale gives consistent readings |
| **FastAPI** | A Python web framework — our server that receives images and returns results | The waiter between the camera and the AI |
| **Ubiquiti** | A brand of networking equipment — our WiFi router connecting the two laptops | The highway between Laptop A and Laptop B |
| **YOLO (YOLOv8)** | A famous object detection AI model — optional upgrade to detect components directly | An AI that can point to objects and name them |
| **Tombstoning** | A defect where a small component stands up vertically on one solder pad | Looks like a tiny tombstone — hence the name |

---

## 7. The Health Index — How We Score a Board

Every board gets a single number between 0 and 1:

```
Health Index = weighted average of (component present? × component height OK?)
```

**In simple terms:**

For each component on the board, we ask two questions:
1. **Is it there?** → presence score (0 = missing, 1 = fully present)
2. **Is it sitting right?** → height penalty (0 = perfect, 1 = totally wrong)

Then we multiply them together. A missing part scores 0. A present-but-tilted part gets a partial penalty.

**Critical parts (like the main chip) count more** than minor parts (like an LED). That's the "weight."

### What the Score Means

| Score | Verdict | What Happens |
|---|---|---|
| **0.95 – 1.00** | ✅ **PASS** | Board is good — ship it |
| **0.80 – 0.94** | ⚠️ **REWORK** | Something minor is off — human should check |
| **Below 0.80** | ❌ **FAIL** | Major problem — quarantine the board |

### Example Scenarios

| Scenario | Health Index | Verdict |
|---|---|---|
| Perfect board, all parts present and seated correctly | 0.98 | ✅ PASS |
| One small capacitor missing | 0.91 | ⚠️ REWORK |
| Main IC chip missing | 0.38 | ❌ FAIL |
| Two resistors missing + one capacitor tilted | 0.72 | ❌ FAIL |

---

## 8. The Pipeline — Step by Step (What the Code Actually Does)

When someone on Laptop A presses SPACE to capture a board photo:

```
Step 1: CAPTURE
  └─ Laptop A webcam takes a photo of the board

Step 2: SEND
  └─ Photo is sent over WiFi to Laptop B's /inspect endpoint

Step 3: ALIGN
  └─ ORB finds matching features between reference and test photo
  └─ Homography warps the test photo to match the reference exactly
  └─ If alignment fails (< 40% feature match) → reject with error message

Step 4: 2D DETECTION (for each component region)
  └─ Crop the same region from both reference and aligned test image
  └─ Apply CLAHE to fix lighting differences
  └─ Calculate SSIM score between the two crops
  └─ SSIM < 0.70 → flag as MISSING

Step 5: DEPTH ESTIMATION
  └─ Run Depth Anything V2 on the test photo → generates depth map
  └─ Load the pre-saved reference depth map
  └─ For each component region, compare depths:
      • Mean depth difference → HEIGHT flag
      • Gradient difference → TILT flag
      • Left/right asymmetry → TOMBSTONE flag

Step 6: HEALTH INDEX
  └─ For each component: HI contribution = weight × presence × (1 - height_penalty)
  └─ Sum all contributions, divide by sum of weights
  └─ Map to verdict: PASS / REWORK / FAIL

Step 7: VISUALIZE
  └─ Draw on the test image:
      🔴 Red circles = missing components
      🟠 Orange triangles = height problems
      🟡 Yellow diamonds = tombstoned
      🟣 Magenta squares = tilted
      🟢 Green checkmarks = everything OK
  └─ Add Health Index banner at top

Step 8: RESPOND
  └─ Send back to Laptop A:
      • JSON with all scores and flags
      • Annotated overlay image
  └─ Write inspection record to audit log (ISO 9001 compliance)
```

---

## 9. What Makes This "Research Grade" (Not Just a Student Project)

| Aspect | Student Project | Our Project |
|---|---|---|
| Testing | "We tested it and it works" | 31-board structured test set with physically measured defects |
| Metrics | "Accuracy is 90%" | Precision, Recall, F1, False Call Rate, Escape Rate — each reported separately |
| Repeatability | Not checked | GR&R study — 90 measurements across 3 lighting conditions |
| Standards | None | IPC-A-610H (industry standard), ISO 9001 (audit trail) |
| Ablation | Not done | 2D-only vs depth-only vs combined — proves each module adds value |
| Audit trail | None | Every inspection logged: UUID, timestamp, SHA-256 hash, per-component results |
| Process monitoring | Not done | DPMO, p-charts, Sigma level — factory-standard SPC |

---

## 10. What Each Team Does — The Simple Version

### Team 4 (Data Engineering) — "The Photographers"
> They set up the camera, take all the photos, build the test set, and manage the network.

**Think of them as:** The ones who collect the exam papers and prepare the answer key.

**Key output:** 31 photographed boards with a CSV file saying exactly what's wrong with each one.

---

### Team 5 (Model Optimization) — "The AI Engineers"
> They build the actual detection algorithms, the depth model, the health index formula, and run all the scientific evaluation.

**Think of them as:** The ones who build and grade the exam — they write the scoring logic.

**Key output:** Working detection pipeline + research-grade evaluation results (precision, recall, GR&R).

---

### Team 6 (AI Deployment) — "The Integrators & Demo Team"
> They wire everything together, build the visual overlay, handle errors, record the backup video, and run the live demo.

**Think of them as:** The ones who build the exam hall, set up the projector, and present the results.

**Key output:** Working end-to-end system + backup demo video + live demo execution.

---

## 11. Talk Track — How to Explain This to Your Team (5 Minutes)

Use this script when you brief everyone:

---

> **"Here's what we're building:"**
>
> We're making an AI system that inspects circuit boards for manufacturing defects. A camera on Laptop A photographs the board, sends the image over WiFi to Laptop B, and Laptop B runs two checks:
>
> **Check 1 — "Is every part there?"**
> We compare the photo against a photo of a perfect board. Any region that looks significantly different = a part is probably missing. This uses SSIM — a similarity score.
>
> **Check 2 — "Is every part sitting correctly?"**
> We run a depth estimation AI model on the photo. It guesses the 3D height of every pixel. If a component's height doesn't match the reference = it might be tilted, raised, or tombstoned.
>
> **Both checks feed into a Health Index** — a single score from 0 to 1. Above 0.95 = PASS. Below 0.80 = FAIL.
>
> **What makes this research-grade:**
> We're not just saying "it works" — we're proving it. We build a 31-board test set with real defects, compute precision/recall/F1, run a repeatability study (GR&R), and follow IPC-A-610 industry standards. Every inspection is logged for ISO 9001 traceability.
>
> **Team 4** handles the camera, network, and test data.
> **Team 5** builds the detection algorithms and runs the evaluation.
> **Team 6** wires it all together and runs the demo.
>
> **The coolest part?** No special hardware. No depth sensor. Just a regular laptop camera. The 3D height check comes from an AI model that estimates depth from a flat 2D photo.

---

## 12. Likely Questions Your Teammates Will Ask

**"Do we need a real PCB?"**
> Not to start — we can print a high-resolution PCB image on paper and use that for development. We switch to a real board once the pipeline works.

**"What if we can't get the depth model to work?"**
> The 2D detection (Check 1) works independently. If depth fails, we ship with 2D-only — that alone is a complete project. The depth module is a bonus.

**"Is this like YOLO?"**
> YOLO detects objects by recognising what they look like (it's been trained on labelled examples). Our baseline approach doesn't need training — it just compares two images. We have YOLO as an optional upgrade track if time allows.

**"What does the Ubiquiti router do?"**
> It creates a private WiFi network between the two laptops with a fixed IP address. This simulates a factory network. Without it, we'd need an Ethernet cable or shared WiFi.

**"Why two laptops instead of one?"**
> To simulate a real factory setup where the camera is on the production line and the server is in a separate room. It also demonstrates network-based architecture to the judges.

**"What if the camera moves between shots?"**
> That's why we tape down the camera position on Day 1 and follow a written SOP. The alignment module also has a quality gate — if the image is too different to align, it rejects it instead of giving wrong results.

**"How long does one inspection take?"**
> About 3–5 seconds on a laptop CPU. In a factory with a GPU, it would be under 1 second.
