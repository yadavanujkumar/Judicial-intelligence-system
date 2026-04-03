"""
Script to generate realistic sample Indian court case data.
Run: python scripts/generate_sample_data.py
"""
import csv
import random
from datetime import datetime, timedelta
import os

COURTS = [
    "Supreme Court of India",
    "Delhi High Court",
    "Bombay High Court",
    "Madras High Court",
    "Calcutta High Court",
    "Allahabad High Court",
    "Karnataka High Court",
    "Rajasthan High Court",
    "Gujarat High Court",
    "Andhra Pradesh High Court",
    "Telangana High Court",
    "Hyderabad High Court",
    "Punjab & Haryana High Court",
    "Madhya Pradesh High Court",
    "Orissa High Court",
]

CASE_TYPES = ["Civil", "Criminal", "Family", "Tax", "Consumer", "Labour", "Constitutional", "Arbitration"]

JUDGES = [
    "Justice D.Y. Chandrachud", "Justice Sanjiv Khanna", "Justice B.R. Gavai",
    "Justice Surya Kant", "Justice Hima Kohli", "Justice A.S. Bopanna",
    "Justice Pamidighantam Sri Narasimha", "Justice J.B. Pardiwala",
    "Justice Manoj Misra", "Justice S.C. Sharma", "Justice Rajesh Bindal",
    "Justice Manmohan", "Justice Prathiba M. Singh", "Justice Yashwant Varma",
    "Justice Anup Jairam Bhambhani", "Justice Navin Chawla", "Justice Vibhu Bakhru",
    "Justice Suresh Kumar Kait", "Justice Dhiraj Singh Thakur", "Justice Amit Bansal",
]

ACTS = [
    "Indian Penal Code (IPC)",
    "Code of Civil Procedure (CPC)",
    "Code of Criminal Procedure (CrPC)",
    "Hindu Marriage Act, 1955",
    "Income Tax Act, 1961",
    "Consumer Protection Act, 2019",
    "Industrial Disputes Act, 1947",
    "Companies Act, 2013",
    "Transfer of Property Act, 1882",
    "Specific Relief Act, 1963",
    "Arbitration and Conciliation Act, 1996",
    "Prevention of Corruption Act, 1988",
    "Negotiable Instruments Act, 1881",
    "Motor Vehicles Act, 1988",
    "Protection of Women from Domestic Violence Act, 2005",
    "Right to Information Act, 2005",
    "Environmental Protection Act, 1986",
    "Insolvency and Bankruptcy Code, 2016",
    "GST Act, 2017",
    "POCSO Act, 2012",
]

OUTCOMES = {
    "Civil": ["Allowed", "Dismissed", "Settled", "Partially Allowed"],
    "Criminal": ["Convicted", "Acquitted", "Bail Granted", "Bail Rejected", "Case Withdrawn"],
    "Family": ["Divorce Granted", "Dismissed", "Settled", "Maintenance Awarded"],
    "Tax": ["Allowed", "Dismissed", "Partially Allowed", "Remanded"],
    "Consumer": ["Allowed", "Dismissed", "Partially Allowed", "Settled"],
    "Labour": ["Allowed", "Dismissed", "Reinstated", "Settled"],
    "Constitutional": ["Allowed", "Dismissed", "Stay Granted"],
    "Arbitration": ["Award Upheld", "Award Set Aside", "Remanded"],
}

PETITIONER_NAMES = [
    "Ramesh Kumar", "Sunita Devi", "M/s Sharma & Sons", "State of Delhi",
    "Union of India", "Rajesh Singh", "Priya Mehta", "Anil Gupta",
    "M/s Tech Solutions Pvt Ltd", "Suresh Prasad", "Meena Kumari",
    "Ashok Verma", "Kavita Sharma", "Vijay Kumar", "Nirmala Devi",
    "M/s Global Traders", "Rakesh Yadav", "Pooja Joshi", "Mohan Lal",
    "Seema Agarwal", "Deepak Nair", "Lalita Bai", "Sanjay Mishra",
    "Geeta Singh", "Harish Chandra", "Usha Rani", "Bharat Lal",
    "Parveen Kumar", "Rekha Devi", "Manoj Tiwari",
]

RESPONDENT_NAMES = [
    "State of Maharashtra", "State of Rajasthan", "Commissioner of Income Tax",
    "M/s ABC Industries", "Ramji Lal", "Sita Devi", "National Insurance Co.",
    "Municipal Corporation", "Delhi Development Authority", "Suresh Kumar",
    "M/s XYZ Enterprises", "Reserve Bank of India", "SEBI", "EPFO",
    "Life Insurance Corporation", "Employees State Insurance Corporation",
    "State Bank of India", "Central Board of Direct Taxes", "RERA Authority",
    "Consumer Forum", "Labour Commissioner", "District Collector",
]

JUDGMENT_TEMPLATES = {
    "Civil": [
        "The petitioner filed a civil suit seeking {relief} against the respondent. The court examined the evidence presented by both parties including documentary and oral testimony. After careful consideration of the legal arguments and precedents cited, the court found {finding}. The court held that {holding}. The petition was {outcome} with {costs}.",
        "The plaintiff instituted a suit for {relief} claiming damages of Rs. {amount}. The trial court had decreed the suit in favour of the plaintiff. On appeal, the High Court examined whether {legal_issue}. The court, relying on the Supreme Court decision in {case_ref}, held that {holding}. The appeal was accordingly {outcome}.",
    ],
    "Criminal": [
        "The accused was charged under Section {section} of the Indian Penal Code for the alleged offence of {offence}. The prosecution examined {num} witnesses to establish its case. The court analysed the evidence on record and found {finding}. Having regard to the totality of evidence, the court held that {holding}. The accused was {outcome}.",
        "The state preferred an appeal against the acquittal of the accused by the trial court. The High Court re-examined the evidence including the testimony of eyewitnesses and forensic reports. The court found {finding} and held that {holding}. The appeal was {outcome}.",
    ],
    "Family": [
        "The petitioner filed a petition for {relief} under Section {section} of the Hindu Marriage Act, 1955. The parties had been married for {years} years and had {children} children. The court examined the grounds alleged and found {finding}. After considering the welfare of the children and the circumstances of the parties, the court held that {holding}. The petition was {outcome}.",
        "The respondent filed an application for maintenance under Section {section} of the Hindu Marriage Act. The applicant was not employed and was dependent on the respondent. The court assessed the income of the respondent and the needs of the applicant. The court held that {holding}. Maintenance of Rs. {amount} per month was {outcome}.",
    ],
    "Tax": [
        "The assessee challenged the assessment order passed by the Assessing Officer under Section {section} of the Income Tax Act, 1961 for the Assessment Year {year}. The dispute related to the disallowance of {amount} as business expenditure. The court examined the nature of the expenditure and the applicable provisions. The court held that {holding}. The appeal was {outcome}.",
        "The revenue appealed against the order of the Income Tax Appellate Tribunal which had ruled in favour of the assessee. The issue involved the taxability of {issue} under the Income Tax Act. The court analysed the statutory provisions and relevant case law. The court held that {holding}. The appeal filed by the revenue was {outcome}.",
    ],
    "Consumer": [
        "The complainant approached the Consumer Forum alleging deficiency in service by the opposite party regarding {service}. The complainant had paid Rs. {amount} for the service/product. The opposite party denied the allegations and contended that {contention}. The Forum found that {finding}. The complaint was {outcome} and the opposite party was directed to pay compensation.",
        "The complainant alleged that the opposite party had sold a defective product and refused to replace or refund the amount. The District Consumer Forum had dismissed the complaint. In appeal, the State Commission examined the evidence and held that {holding}. The opposite party was directed to {direction}.",
    ],
    "Labour": [
        "The workman challenged the termination of his services by the management under the Industrial Disputes Act, 1947. The labour court had held in favour of the workman. The management challenged this award before the High Court. The court examined whether {legal_issue}. The court held that {holding}. The writ petition was {outcome}.",
        "The petitioner was a contractual employee who claimed regularization of services. The court examined the nature of work and the period of employment. Relying on the Supreme Court's guidelines in Umadevi's case, the court held that {holding}. The petition was {outcome}.",
    ],
    "Constitutional": [
        "A writ petition was filed challenging the constitutional validity of {provision} as being violative of Articles {articles} of the Constitution of India. The petitioner contended that {contention}. The respondent argued that {defense}. The court examined the provision in light of the constitutional provisions and precedents. The court held that {holding}. The petition was {outcome}.",
        "The petitioner sought mandamus directing the respondent authority to {direction}. The court found that {finding}. In view of the settled legal position, the court directed the respondent to {relief}. The petition was disposed of with these directions.",
    ],
    "Arbitration": [
        "The petitioner challenged the arbitral award dated {date} passed by the sole arbitrator under Section 34 of the Arbitration and Conciliation Act, 1996. The dispute related to {dispute}. The court examined whether the award suffered from any patent illegality or was in conflict with public policy. The court found {finding}. The petition was {outcome}.",
        "The respondent's application under Section 9 of the Arbitration and Conciliation Act, 1996 for interim measures was allowed by the trial court. The petitioner challenged this order. The High Court examined whether the balance of convenience lay in favour of granting interim relief. The court held that {holding}. The appeal was {outcome}.",
    ],
}


def generate_judgment_text(case_type: str, outcome: str) -> str:
    templates = JUDGMENT_TEMPLATES.get(case_type, JUDGMENT_TEMPLATES["Civil"])
    template = random.choice(templates)

    replacements = {
        "{relief}": random.choice(["specific performance", "injunction", "declaration", "recovery of money", "possession of property"]),
        "{amount}": f"{random.randint(1, 100) * 50000:,}",
        "{finding}": random.choice([
            "that the evidence on record clearly established the petitioner's case",
            "that the respondent had failed to discharge its legal obligation",
            "that there was no merit in the contentions raised by the petitioner",
            "that the impugned order was passed without following due process",
            "that the petitioner had established a prima facie case",
        ]),
        "{holding}": random.choice([
            "the impugned order was liable to be set aside",
            "the petitioner was entitled to the relief prayed for",
            "the respondent had not committed any illegality",
            "the terms of the contract had been breached by the respondent",
            "the statutory provisions had been complied with",
        ]),
        "{outcome}": outcome.lower(),
        "{costs}": random.choice(["costs", "no order as to costs"]),
        "{case_ref}": random.choice([
            "AIR 2019 SC 1234", "2021 SCC 456", "(2020) 5 SCC 789",
            "AIR 2018 SC 567", "(2022) 3 SCC 123",
        ]),
        "{legal_issue}": random.choice([
            "the lower court had correctly appreciated the evidence",
            "the statutory conditions had been fulfilled",
            "the limitation period had expired",
            "there was a valid cause of action",
        ]),
        "{section}": str(random.randint(3, 500)),
        "{offence}": random.choice(["murder", "theft", "cheating", "assault", "criminal breach of trust"]),
        "{num}": str(random.randint(3, 15)),
        "{years}": str(random.randint(1, 25)),
        "{children}": str(random.randint(0, 4)),
        "{year}": f"{random.randint(2015, 2022)}-{random.randint(16, 23)}",
        "{issue}": random.choice(["interest income", "capital gains", "deemed dividend", "business income", "royalty"]),
        "{service}": random.choice(["insurance claim", "banking service", "medical treatment", "real estate", "telecom service"]),
        "{contention}": random.choice([
            "the service had been rendered as per the agreed terms",
            "there was no deficiency in service",
            "the complainant had violated the terms of the agreement",
        ]),
        "{direction}": random.choice(["refund the amount with interest", "replace the defective product", "provide the promised service"]),
        "{provision}": random.choice(["Section 377 IPC", "Section 66A IT Act", "Section 124A IPC"]),
        "{articles}": random.choice(["14 and 19", "21 and 22", "14, 19 and 21", "32"]),
        "{contention}": "the impugned provision was arbitrary and unconstitutional",
        "{defense}": "the provision was a reasonable restriction in public interest",
        "{date}": f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2019, 2023)}",
        "{dispute}": random.choice(["non-payment of contract price", "defective construction work", "breach of supply agreement"]),
    }

    text = template
    for key, val in replacements.items():
        text = text.replace(key, val)
    return text


def generate_cases(n: int = 250) -> list[dict]:
    cases = []
    start_date_range = datetime(2018, 1, 1)
    end_date_range = datetime(2024, 1, 1)

    for i in range(1, n + 1):
        case_type = random.choice(CASE_TYPES)
        filing_date = start_date_range + timedelta(days=random.randint(0, (end_date_range - start_date_range).days))
        duration_days = random.randint(30, 3000)
        decision_date = filing_date + timedelta(days=duration_days)
        outcome = random.choice(OUTCOMES.get(case_type, ["Allowed", "Dismissed"]))
        court = random.choice(COURTS)
        judge = random.choice(JUDGES)
        act = random.choice(ACTS)
        num_hearings = max(1, int(duration_days / random.uniform(30, 90)))
        judgment_text = generate_judgment_text(case_type, outcome)

        prefix_map = {
            "Civil": "CS", "Criminal": "CR", "Family": "FAM",
            "Tax": "TAX", "Consumer": "CON", "Labour": "LAB",
            "Constitutional": "WP", "Arbitration": "ARB",
        }
        prefix = prefix_map.get(case_type, "CASE")
        case_id = f"{prefix}/{random.randint(1000, 9999)}/{filing_date.year}"

        cases.append({
            "case_id": case_id,
            "court": court,
            "case_type": case_type,
            "filing_date": filing_date.strftime("%Y-%m-%d"),
            "decision_date": decision_date.strftime("%Y-%m-%d"),
            "duration_days": duration_days,
            "judge": judge,
            "petitioner": random.choice(PETITIONER_NAMES),
            "respondent": random.choice(RESPONDENT_NAMES),
            "act": act,
            "outcome": outcome,
            "num_hearings": num_hearings,
            "judgment_text": judgment_text,
        })
    return cases


def main():
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_cases.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cases = generate_cases(250)
    fieldnames = [
        "case_id", "court", "case_type", "filing_date", "decision_date",
        "duration_days", "judge", "petitioner", "respondent", "act",
        "outcome", "num_hearings", "judgment_text",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cases)

    print(f"Generated {len(cases)} cases -> {output_path}")


if __name__ == "__main__":
    main()
