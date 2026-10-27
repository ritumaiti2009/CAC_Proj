# Textora Portal

Made for Congressional App Challenge 2026

## Overview
This website was developed for the Congressional App Challenge to address the problem of unequal access to educational resources. It allows students to donate, exchange, and request textbooks through a centralized online platform, making educational materials more accessible and affordable.

## Real-World Scenario
Many students struggle to obtain required textbooks due to their high costs or limited availability. Some textbooks cost over $150, forcing students to rely on older classmates, purchase expensive copies, or resort to pirated versions. This platform provides a convenient way for students to connect with others who have textbooks they no longer need, reducing educational expenses while encouraging the reuse of academic resources.

## Features
1. View a list of available textbooks posted by other students.
2. Search for textbooks using keywords, titles, or subjects.
3. Post textbooks available for donation or exchange.
4. Request textbooks from other students.
5. Sign in to manage posts and streamline interactions.
6. Allow administrator accounts to approve or delete posts to maintain a safe platform.

## Technologies Used

**Backend:**
- Python v3.9.6
- Flask
  - Flask-Mail
  - Werkzeug
- SQLite3
- Jinja2
- JavaScript

**Frontend:**
- HTML5
- CSS3
- Bootstrap 5

**Development Tools:**
- Git & GitHub for version control and collaboration
- Visual Studio Code
- OpenAI Codex for development assistance, including interface improvements and more technically complex integrations

## Future Goals
We aim to expand the platform beyond individual schools, allowing students across districts and eventually different countries to exchange educational resources. By connecting students with available textbooks, we hope to reduce educational inequality, prevent unnecessary textbook waste, and help more students obtain the materials they need to succeed.
**How to run locally**
1. Download repository
2. Open using Visual Code Studio or similar IDE
3. Create a Virtual Environment
4. Install dependencies from requirements.txt
5. Create a .env file with 'MAIL_USERNAME' (an email) and 'MAIL_PASSWORD' (an APP password); this is to send an email.
6. Activate Virtual Environment
7. Run app.py using 'python app.py'

**Credits**
* Third-party technologies
    * Flask - BSD-3-Clause License
    * Other Flask and Python Libraries - All are distributed under permissive open-source licenses (primarily MIT, BSD, or Apache 2.0).
    * Black – MIT License
    * Djlint – MIT License
    * Bootstrap – MIT License
* Visuals
    * "Logo.png" (Village Vikings Logo) – Copyrighted @ 2019 The Village School. Used under Fair Use for educational and non-commercial purposes.
    * Homepage Background (The Village School Top View) – Copyrighted @ 2023 The Village School. Used under Fair Use for educational and non-commercial purposes.
    * Emojis – Copyrighted @ 2026 Apple Inc. Used under Fair Use for educational and non-commercial purposes.
    * Embedded Google Map View – Copyrighted @ 2026 Alphabet Inc. Used under Fair Use for educational and non-commercial purposes.
    * Atkinson Hyperlegible Font – SIL Open Font License
