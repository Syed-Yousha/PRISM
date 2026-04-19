# PRISM (Personalized Resource for Intelligent Study & Mastery)

[](https://github.com/Syed-Yousha/PRISM)
[](https://www.google.com/search?q=%23)
[](https://www.google.com/search?q=%23)

An AI-powered study platform designed to transform a student's syllabus, lecture notes, and past papers into personalized lecture videos, quizzes, and guided courses.

## 📖 About The Project

University students often struggle with fragmented, generic online resources that fail to align with their exact syllabus or examination patterns. PRISM solves this by acting as an intelligent study companion. By leveraging LLMs and video generation pipelines, it converts standard course materials into a structured, interactive, and exam-ready learning pathway—mirroring the classroom experience with the speed and personalization of AI.

## 📂 Repository Structure

This repository is split into core modular directories handling different aspects of the pipeline:

  * **`PRISM-A/`**: Core frontend/backend logic or primary module A.
  * **`PRISM-B/`**: Secondary services, AI processing pipeline, or module B.
  * **`Challenges.txt`**: Ongoing development challenges, roadblocks, and solutions tracking.

## ✨ Key Features

  * **Live AI Tutor (Quick-Help Mode):** Type any topic (e.g., "Trigonometry") and instantly receive a simplified AI-generated lecture video with voice-over and visuals.
  * **Course Generator:** Upload a course outline to automatically generate a navigable learning pathway with chapters, subtopics, video lectures, and quizzes.
  * **AI Tutor (Blackboard Mode):** Get animated, blackboard-style visual explanations generated via Manim for complex queries.
  * **Automated Assessments:** Auto-generated topic-specific MCQs and true/false questions linked to lecture content.
  * **AI Flashcards:** Intelligent flashcard generation for spaced repetition and active recall.
  * **Progress Dashboard:** Comprehensive tracking of learning progress, quiz scores, completed topics, and weak areas.

## 🛠 Tech Stack

**Core Pipeline & AI:**

  * **Python** (99.2% of the codebase)
  * **OpenAI GPT-4 API** (Script generation, intent detection, QA agents)
  * **Manim** (Mathematical Animation Engine for visual explanations)
  * **ElevenLabs / Google TTS** (Voice-over synthesis)
  * **FFmpeg** (Video/Audio compilation and rendering)

**Web Application:**

  * **Frontend:** React.js / Next.js, Tailwind CSS
  * **Backend:** FastAPI (Python) / Node.js
  * **Database & Storage:** MySQL / PostgreSQL, Redis (Caching), AWS S3 (Video Storage)

## ⚙️ Architecture & Data Flow

PRISM utilizes a multi-agent AI architecture:

1.  **Intent Detection:** Determines if the query is a general chat or syllabus-specific.
2.  **Notes & Script Agents:** Extracts topics and generates a frame-by-frame instructional script.
3.  **QA Agent:** Generates relevant quiz questions to test understanding.
4.  **Video Generation Agent:** Uses Manim and TTS to render slides and audio, finally assembling them via FFmpeg into a playable MP4.

## 👨‍💻 Team Members

  * **Syed Yousha** - AI Engineer & Project Lead
  * **Yasir Memon** - Graphic Designer (UI/UX)
  * **Taha Farooqui** - Website Developer

*Supervised by: Miss Javeria Farooq*
