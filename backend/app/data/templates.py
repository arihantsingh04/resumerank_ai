"""Entry-level BTech role templates (D-38). Add a role by adding one dict.

`icon` is a lucide-react icon name used by the frontend.
"""

from __future__ import annotations

from typing import TypedDict


class Template(TypedDict):
    id: str
    title: str
    category: str
    icon: str
    summary: str
    seniority: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    min_years: float | None
    description: str


ENTRY = "Entry level · 0–2 yrs"
EDU = "B.Tech / B.E. in Computer Science, IT, ECE or a related field."


def _jd(title: str, intro: str, duties: list[str], required: list[str], nice: list[str]) -> str:
    return (
        f"{title}\n\n{intro}\n\nWhat you'll do\n"
        + "\n".join(f"- {d}" for d in duties)
        + "\n\nRequirements\n- "
        + EDU
        + "\n- 0–2 years of experience, including internships and strong projects.\n"
        + "\n".join(f"- Hands-on with {s}." for s in required)
        + "\n\nNice to have\n"
        + "\n".join(f"- {s}" for s in nice)
    )


def _t(id_, title, category, icon, summary, duties, required, nice) -> Template:
    return Template(
        id=id_, title=title, category=category, icon=icon, summary=summary, seniority=ENTRY,
        required_skills=required, nice_to_have_skills=nice, min_years=None,
        description=_jd(title, summary, duties, required, nice),
    )


TEMPLATES: list[Template] = [
    _t("backend", "Backend Developer", "Software", "server",
       "Build and run the APIs and services behind a product used by thousands of people.",
       ["Design and build REST APIs and background jobs.", "Model data and write efficient queries.",
        "Write automated tests and take part in code reviews.", "Debug and fix production issues with the team."],
       ["Python", "SQL", "REST APIs", "Git", "Data Structures", "OOP"],
       ["FastAPI", "Django", "PostgreSQL", "Docker", "Redis", "AWS"]),
    _t("frontend", "Frontend Developer", "Software", "layout-template",
       "Craft fast, accessible web interfaces that people enjoy using.",
       ["Build responsive UI components from Figma designs.", "Integrate REST APIs and manage client state.",
        "Improve performance and accessibility.", "Write component and end-to-end tests."],
       ["HTML", "CSS", "JavaScript", "React", "Responsive Design", "Git"],
       ["TypeScript", "Next.js", "Tailwind CSS", "Redux", "Jest", "Web Accessibility", "Figma"]),
    _t("full-stack", "Full Stack Developer", "Software", "layers",
       "Ship features end to end, from the database to the browser.",
       ["Build product features across frontend and backend.", "Design APIs and database schemas.",
        "Deploy and monitor services.", "Collaborate with design and product on scope."],
       ["JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git"],
       ["TypeScript", "Express.js", "MongoDB", "PostgreSQL", "Docker", "AWS", "Next.js"]),
    _t("android", "Android Developer", "Mobile", "smartphone",
       "Build native Android apps with modern Kotlin and Jetpack libraries.",
       ["Build screens and features in Kotlin.", "Integrate REST APIs and local storage.",
        "Fix crashes and improve app performance.", "Publish releases to the Play Store."],
       ["Kotlin", "Android", "Android Studio", "REST APIs", "Git", "OOP"],
       ["Jetpack Compose", "Room", "Firebase", "Java", "Unit Testing", "App Store Deployment"]),
    _t("ios", "iOS Developer", "Mobile", "apple",
       "Create polished native iPhone apps with Swift.",
       ["Build features in Swift and SwiftUI.", "Integrate APIs and handle offline data.",
        "Profile and improve performance.", "Ship builds through TestFlight and the App Store."],
       ["Swift", "iOS", "Xcode", "SwiftUI", "REST APIs", "Git"],
       ["UIKit", "Core Data", "Firebase", "Unit Testing", "Push Notifications", "App Store Deployment"]),
    _t("flutter", "Flutter Developer", "Mobile", "tablet-smartphone",
       "Build beautiful cross-platform apps for Android and iOS from one Dart codebase.",
       ["Build UI with Flutter widgets.", "Manage state and integrate REST APIs.",
        "Use Firebase for auth, storage and notifications.", "Release to Play Store and App Store."],
       ["Flutter", "Dart", "REST APIs", "Firebase", "Git", "OOP"],
       ["Provider", "Bloc", "Riverpod", "Android", "iOS", "Unit Testing", "App Store Deployment"]),
    _t("react-native", "React Native Developer", "Mobile", "atom",
       "Build cross-platform mobile apps with React Native and JavaScript.",
       ["Build screens and navigation in React Native.", "Integrate APIs and manage app state.",
        "Debug on Android and iOS devices.", "Ship OTA updates and store releases."],
       ["React Native", "JavaScript", "React", "REST APIs", "Git"],
       ["TypeScript", "Redux", "Expo", "Firebase", "Jest", "Android", "iOS"]),
    _t("devops", "DevOps Engineer", "Infrastructure", "infinity",
       "Automate how code is built, tested and shipped, and keep systems healthy.",
       ["Build and maintain CI/CD pipelines.", "Containerise services and manage deployments.",
        "Set up monitoring, logging and alerts.", "Automate infrastructure with code."],
       ["Linux", "Docker", "CI/CD", "Git", "Bash", "Networking"],
       ["Kubernetes", "Terraform", "AWS", "Jenkins", "GitHub Actions", "Prometheus", "Grafana", "Python"]),
    _t("cloud", "Cloud Engineer", "Infrastructure", "cloud",
       "Design and operate secure, cost-efficient cloud infrastructure.",
       ["Provision and manage cloud resources.", "Configure networking, IAM and storage.",
        "Automate deployments with infrastructure as code.", "Monitor cost, uptime and security."],
       ["AWS", "Linux", "Networking", "IAM", "Bash", "Git"],
       ["Azure", "GCP", "Terraform", "Docker", "Kubernetes", "Serverless", "Python"]),
    _t("data-analyst", "Data Analyst", "Data", "bar-chart-3",
       "Turn raw data into dashboards and insights that drive decisions.",
       ["Write SQL to extract and clean data.", "Build dashboards and reports.",
        "Analyse trends and present findings to stakeholders.", "Define and track KPIs."],
       ["SQL", "Excel", "Statistics", "Data Visualization", "Python"],
       ["Power BI", "Tableau", "Pandas", "Data Cleaning", "A/B Testing", "BigQuery"]),
    _t("ml-engineer", "Machine Learning Engineer", "Data", "brain-circuit",
       "Build, evaluate and deploy machine learning models that solve real problems.",
       ["Prepare data and engineer features.", "Train and evaluate ML models.",
        "Deploy models behind APIs and monitor them.", "Read papers and prototype new approaches."],
       ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "Statistics"],
       ["Deep Learning", "PyTorch", "TensorFlow", "NLP", "LLMs", "MLOps", "Docker", "SQL"]),
    _t("qa-sdet", "QA / SDET Engineer", "Quality & Security", "bug",
       "Make sure every release works by designing and automating tests.",
       ["Write test plans and test cases.", "Automate UI and API tests.",
        "Track and report bugs clearly.", "Run regression suites in CI."],
       ["Manual Testing", "Test Cases", "Test Automation", "API Testing", "SQL", "Git"],
       ["Selenium", "Playwright", "Cypress", "Postman", "Java", "Python", "Bug Tracking", "CI/CD"]),
    _t("cybersecurity", "Cybersecurity Analyst", "Quality & Security", "shield-check",
       "Protect systems and data by finding and fixing security weaknesses.",
       ["Monitor alerts and investigate incidents.", "Run vulnerability assessments.",
        "Harden systems and review configurations.", "Document findings and fixes."],
       ["Network Security", "Linux", "Networking", "OWASP", "Vulnerability Assessment"],
       ["Penetration Testing", "Burp Suite", "Wireshark", "Nmap", "SIEM", "Python", "Cryptography", "Security+"]),
    _t("embedded-iot", "Embedded / IoT Engineer", "Hardware", "cpu",
       "Write firmware that makes connected devices sense, think and talk.",
       ["Develop firmware for microcontrollers.", "Interface sensors over UART, SPI and I2C.",
        "Connect devices to the cloud.", "Debug hardware with lab tools."],
       ["Embedded C", "Microcontrollers", "UART", "SPI", "I2C", "Debugging"],
       ["RTOS", "IoT", "MQTT", "ESP32", "Arduino", "Raspberry Pi", "PCB Design", "Python"]),
]
BY_ID: dict[str, Template] = {t["id"]: t for t in TEMPLATES}
