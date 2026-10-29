"""Tech-skill catalogue for reading requirements out of a JD without AI (D-37).

Each entry is (canonical name, extra aliases). Matching is case-insensitive with symbol-aware word
boundaries, except entries marked case-sensitive (single letters / common words).
"""

from __future__ import annotations

import re

_S = str
CATALOG: list[tuple[_S, tuple[_S, ...]]] = [
    # Languages
    ("Python", ()),
    ("Java", ()),
    ("JavaScript", ("js",)),
    ("TypeScript", ("ts",)),
    ("C++", ("cpp",)),
    ("C#", ("csharp",)),
    ("Go", ("golang",)),
    ("Rust", ()),
    ("Kotlin", ()),
    ("Swift", ()),
    ("Dart", ()),
    ("PHP", ()),
    ("Ruby", ()),
    ("Scala", ()),
    ("Objective-C", ()),
    ("Bash", ("shell scripting", "shell script")),
    ("PowerShell", ()),
    ("SQL", ()),
    ("MATLAB", ()),
    ("Embedded C", ()),
    ("Verilog", ()),
    ("VHDL", ()),
    # Web / backend
    ("HTML", ("html5",)),
    ("CSS", ("css3",)),
    ("Tailwind CSS", ("tailwind",)),
    ("Sass", ("scss",)),
    ("React", ("reactjs", "react.js")),
    ("Next.js", ("nextjs",)),
    ("Angular", ("angularjs",)),
    ("Vue.js", ("vue", "vuejs")),
    ("Redux", ()),
    ("Node.js", ("nodejs", "node js")),
    ("Express.js", ("expressjs", "express js")),
    ("NestJS", ()),
    ("Django", ()),
    ("Flask", ()),
    ("FastAPI", ()),
    ("Spring Boot", ("springboot",)),
    ("Spring", ()),
    ("Hibernate", ()),
    (".NET", ("dotnet", "asp.net")),
    ("Laravel", ()),
    ("Ruby on Rails", ("rails",)),
    ("REST APIs", ("rest api", "restful", "restful apis", "rest")),
    ("GraphQL", ()),
    ("gRPC", ()),
    ("Microservices", ("microservice",)),
    ("WebSockets", ("websocket",)),
    ("System Design", ()),
    ("Webpack", ()),
    ("Vite", ()),
    ("Responsive Design", ("responsive web design",)),
    ("Web Accessibility", ("accessibility", "wcag", "a11y")),
    ("Figma", ()),
    ("OAuth", ("oauth2", "jwt")),
    # Data stores / messaging
    ("PostgreSQL", ("postgres",)),
    ("MySQL", ()),
    ("MongoDB", ("mongo",)),
    ("Redis", ()),
    ("SQLite", ()),
    ("NoSQL", ()),
    ("Firebase", ()),
    ("DynamoDB", ()),
    ("Elasticsearch", ()),
    ("Kafka", ("apache kafka",)),
    ("RabbitMQ", ()),
    ("Cassandra", ()),
    # Mobile
    ("Flutter", ()),
    ("React Native", ()),
    ("Android", ("android sdk",)),
    ("iOS", ()),
    ("SwiftUI", ()),
    ("UIKit", ()),
    ("Jetpack Compose", ()),
    ("Xcode", ()),
    ("Android Studio", ()),
    ("Room", ()),
    ("Core Data", ()),
    ("Provider", ()),
    ("Bloc", ()),
    ("Riverpod", ()),
    ("Expo", ()),
    ("Push Notifications", ("fcm", "apns")),
    ("App Store Deployment", ("play store", "app store")),
    # DevOps / cloud
    ("Docker", ()),
    ("Kubernetes", ("k8s",)),
    ("Helm", ()),
    ("Terraform", ()),
    ("Ansible", ()),
    ("Jenkins", ()),
    ("GitHub Actions", ()),
    ("GitLab CI", ()),
    ("CI/CD", ("ci cd", "cicd", "continuous integration")),
    ("AWS", ("amazon web services",)),
    ("Azure", ("microsoft azure",)),
    ("GCP", ("google cloud", "google cloud platform")),
    ("Linux", ()),
    ("Nginx", ()),
    ("Prometheus", ()),
    ("Grafana", ()),
    ("ELK Stack", ("elk",)),
    ("Monitoring", ("observability",)),
    ("Serverless", ("aws lambda", "lambda")),
    ("CloudFormation", ()),
    ("Networking", ("computer networks",)),
    ("TCP/IP", ()),
    ("DNS", ()),
    ("Load Balancing", ("load balancer",)),
    ("Git", ()),
    ("GitHub", ()),
    ("Infrastructure as Code", ("iac",)),
    ("SRE", ("site reliability",)),
    ("Incident Response", ()),
    # Data / ML
    ("Excel", ("ms excel", "microsoft excel")),
    ("Power BI", ("powerbi",)),
    ("Tableau", ()),
    ("Looker", ()),
    ("Pandas", ()),
    ("NumPy", ()),
    ("Matplotlib", ()),
    ("Seaborn", ()),
    ("Statistics", ("statistical",)),
    ("Data Visualization", ("data visualisation", "dashboards", "dashboard")),
    ("Data Cleaning", ()),
    ("ETL", ()),
    ("Data Warehousing", ("data warehouse",)),
    ("Snowflake", ()),
    ("BigQuery", ()),
    ("Apache Spark", ("spark", "pyspark")),
    ("Hadoop", ()),
    ("Airflow", ("apache airflow",)),
    ("Machine Learning", ("ml",)),
    ("Deep Learning", ("dl",)),
    ("Scikit-learn", ("sklearn", "scikit learn")),
    ("TensorFlow", ()),
    ("PyTorch", ()),
    ("Keras", ()),
    ("NLP", ("natural language processing",)),
    ("Computer Vision", ("opencv",)),
    ("LLMs", ("llm", "large language models", "generative ai", "genai")),
    ("MLOps", ()),
    ("Model Deployment", ()),
    ("Feature Engineering", ()),
    ("A/B Testing", ("ab testing",)),
    ("Jupyter", ("jupyter notebook",)),
    # QA
    ("Selenium", ()),
    ("Cypress", ()),
    ("Playwright", ()),
    ("Appium", ()),
    ("JUnit", ()),
    ("TestNG", ()),
    ("PyTest", ()),
    ("Jest", ()),
    ("Postman", ()),
    ("API Testing", ()),
    ("Manual Testing", ()),
    ("Test Automation", ("automation testing", "automated testing")),
    ("Unit Testing", ("unit tests",)),
    ("Performance Testing", ("load testing", "jmeter")),
    ("Test Cases", ("test case design",)),
    ("Bug Tracking", ("jira",)),
    # Security
    ("OWASP", ("owasp top 10",)),
    ("Penetration Testing", ("pen testing", "pentesting", "vapt")),
    ("Burp Suite", ()),
    ("Wireshark", ()),
    ("Nmap", ()),
    ("Metasploit", ()),
    ("SIEM", ("splunk",)),
    ("Cryptography", ("encryption",)),
    ("Vulnerability Assessment", ()),
    ("Network Security", ()),
    ("Firewalls", ("firewall",)),
    ("IAM", ("identity and access management",)),
    ("Security+", ()),
    # Embedded / IoT
    ("Microcontrollers", ("microcontroller", "stm32", "8051", "avr")),
    ("ARM Cortex", ("arm",)),
    ("RTOS", ("freertos",)),
    ("Arduino", ()),
    ("Raspberry Pi", ()),
    ("UART", ()),
    ("SPI", ()),
    ("I2C", ()),
    ("CAN", ()),
    ("IoT", ("internet of things",)),
    ("MQTT", ()),
    ("PCB Design", ("pcb",)),
    ("Device Drivers", ("device driver",)),
    ("Linux Kernel", ()),
    ("ESP32", ()),
    ("Sensors", ("sensor",)),
    ("Oscilloscope", ()),
    ("Firmware", ()),
    # Fundamentals / process
    ("Data Structures", ("dsa",)),
    ("Algorithms", ()),
    ("OOP", ("object oriented", "object-oriented")),
    ("DBMS", ("database management",)),
    ("Operating Systems", ()),
    ("Agile", ("scrum",)),
    ("Code Review", ("code reviews",)),
    ("Debugging", ()),
    ("Problem Solving", ()),
]
_CASE_SENSITIVE = {
    "Go",
    "Rust",
    "Swift",
    "Room",
    "Provider",
    "Bloc",
    "Expo",
    "Spring",
    "CAN",
    "SPI",
    "Ruby",
    "Sensors",
}
_CASE_SENSITIVE_ALIASES = {"rest", "arm", "ml", "dl", "ts", "js"}

_NICE = re.compile(
    r"nice[\s-]to[\s-]have|good[\s-]to[\s-]have|preferred|bonus|\ba plus\b"
    r"|added advantage|optional|desirable",
    re.IGNORECASE,
)
_REQUIRED_HEADING = re.compile(
    r"must[\s-]have|required|requirements|qualifications|responsibilities|what you|you will|skills",
    re.IGNORECASE,
)


def _pattern(term: str, case_sensitive: bool) -> re.Pattern[str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"(?<![\w+#.]){re.escape(term)}(?![\w+#]|\.\w)", flags)


_PATTERNS: list[tuple[str, list[re.Pattern[str]]]] = []
for _name, _aliases in CATALOG:
    pats = [_pattern(_name, _name in _CASE_SENSITIVE)]
    for alias in _aliases:
        cs = alias in _CASE_SENSITIVE_ALIASES
        pats.append(_pattern(alias.upper() if cs else alias, cs))
    _PATTERNS.append((_name, pats))


def find_skills(text: str) -> list[str]:
    """Catalogue skills mentioned in `text`, in catalogue order."""
    return [name for name, pats in _PATTERNS if any(p.search(text) for p in pats)]


def _segments(jd: str) -> list[tuple[str, bool]]:
    """Split a JD into (segment, is_nice_to_have). A 'Nice to have:' heading applies to following lines."""
    out: list[tuple[str, bool]] = []
    in_nice_section = False
    for line in jd.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        is_heading = stripped.endswith(":") or len(stripped.split()) <= 4
        if is_heading and _NICE.search(stripped):
            in_nice_section = True
        elif is_heading and _REQUIRED_HEADING.search(stripped):
            in_nice_section = False
        for sentence in re.split(r"(?<=[.;!?])\s+", stripped):
            out.append((sentence, in_nice_section or bool(_NICE.search(sentence))))
    return out


def extract_skills(jd: str) -> tuple[list[str], list[str]]:
    """(required, nice_to_have) skills found in a JD. A skill seen anywhere as required stays required."""
    required: list[str] = []
    nice: list[str] = []
    for segment, is_nice in _segments(jd):
        for skill in find_skills(segment):
            target = nice if is_nice else required
            if skill not in target:
                target.append(skill)
    nice = [s for s in nice if s not in required]
    return required[:25], nice[:15]


_YEARS = re.compile(r"(\d{1,2})\s*(?:\+|-\s*\d{1,2}|to\s*\d{1,2})?\s*\+?\s*(?:years|yrs)", re.IGNORECASE)


def extract_min_years(text: str) -> float | None:
    m = _YEARS.search(text)
    return float(m.group(1)) if m else None
