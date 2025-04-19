# 🎓 CanvasCord

**CanvasCord** is a custom-built Discord bot that integrates directly with the Canvas Learning Management System (LMS) to help students and professors stay informed, organized, and connected.

Instead of switching between Canvas and Discord, users can receive assignment updates, deadlines, announcements, grades, and reminders—all within Discord, where many students already collaborate.

---

## 🚀 What Does It Do?

CanvasCord connects your **Canvas account** to your **Discord account** and delivers personalized, real-time academic updates in an easy-to-use format.

### Core Features:
- 🔔 Real-time Canvas notifications (assignments, grades, announcements)
- 🧠 Interactive reminders and study tools
- 🛠️ Custom notification preferences per user
- 🧾 Calendar integration for due dates and events
- 🔒 FERPA-compliant data handling

---

## ⚙️ How It Works

CanvasCord runs on a **Raspberry Pi 5** and connects to both **Canvas** and **Discord** using secure APIs.

### Key Components:
- **Canvas API**: The bot uses OAuth 2.0 to let users securely connect their Canvas accounts. It pulls assignment and course data on request or at regular intervals.
- **Discord Bot API**: The bot responds to slash commands (`/grades`, `/reminders`, etc.) and sends updates directly to users or specific channels.
- **MySQL Database**: Stores encrypted user tokens, preferences, reminders, and cached course data. No personal student data is stored—only what's needed for functionality.
- **AES Encryption**: Protects Canvas API tokens using industry-standard encryption methods.

### Security Highlights:
- Only ports 443 (HTTPS), 53 (DNS), and optionally 22 (SSH) are open
- All API communication is encrypted over HTTPS
- Tokens are encrypted at rest with AES
- User data is never shared in public channels
- Users can revoke access at any time with a logout command

---

## 🧪 Example Use Cases

- A student types `/assignments` and sees upcoming Canvas assignments right in Discord
- A professor schedules weekly class reminders via the bot
- A user sets a personal study reminder that pings them every Thursday

---

CanvasCord brings the classroom to where collaboration already happens—**Discord**—and helps users stay on track without checking multiple platforms.

### Required Libraries
```
pip install discord.py
pip install canvasapi
pip install mysql-connector-python
pip install beautifulsoup4
```