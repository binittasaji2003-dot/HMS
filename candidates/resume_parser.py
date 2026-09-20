import io
import re
import zlib
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple


INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Chandigarh", "Puducherry", "Jammu and Kashmir", "Ladakh"
]

SKILL_HEADER_WORDS = {
    "web", "development", "frameworks", "database", "management", "tools",
    "core concepts", "programming", "languages", "technologies", "skills",
    "technical skills", "libraries", "platforms", "certifications", "academics",
    "projects", "summary", "experience", "education"
}

COMMON_SKILLS = [
    "Python", "Django", "Flask", "FastAPI", "JavaScript", "TypeScript", "React",
    "Angular", "Vue", "Node.js", "Express", "HTML", "HTML5", "CSS", "CSS3",
    "Bootstrap", "Tailwind", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "GitLab",
    "CI/CD", "REST API", "RESTful", "GraphQL", "Java", "Spring Boot", "Spring", "C", "C++", "C#",
    ".NET", "PHP", "Laravel", "Ruby", "Rails", "Go", "Golang", "Rust", "Swift",
    "Kotlin", "Android", "iOS", "Flutter", "React Native", "Machine Learning",
    "Deep Learning", "Data Analysis", "Data Analytics", "Data Science", "Pandas", "NumPy", "Scikit-Learn",
    "TensorFlow", "PyTorch", "NLP", "Computer Vision", "SQL", "NoSQL", "Linux",
    "Agile", "Scrum", "Jira", "Selenium", "Unit Testing", "Microservices",
    "DevOps", "JSON", "XML", "Kafka", "Elasticsearch", "Jenkins", "Terraform",
    "Project Management", "Communication", "Problem Solving", "Leadership",
    "Cybersecurity", "Networking", "Tableau", "Power BI", "Excel", "OOP", "DBMS", "VS Code"
]

DEGREE_MAPPINGS = [
    (r"\b(Ph\.?D|Doctorate|Doctor of Philosophy)\b", "Doctorate / PhD", "Doctorate / PhD", "Other"),
    (r"\b(M\.?Tech|Master of Technology)\b", "Master's", "M.Tech", "Engineering"),
    (r"\b(M\.?E\.?|Master of Engineering)\b", "Master's", "M.E.", "Engineering"),
    (r"\b(Master of Science|M\.?Sc)\b", "Master's", "M.Sc", "Computer Science"),
    (r"\b(M\.?C\.?A|Master of Computer Applications)\b", "Master's", "MCA", "Computer Applications"),
    (r"\b(M\.?B\.?A|Master of Business Administration)\b", "Master's", "MBA", "Business Administration"),
    (r"\b(M\.?Com|Master of Commerce)\b", "Master's", "M.Com", "Commerce"),
    (r"\b(M\.?A|Master of Arts)\b", "Master's", "M.A.", "Other"),
    (r"\b(B\.?Tech|Bachelor of Technology)\b", "Bachelor's", "B.Tech", "Engineering"),
    (r"\b(B\.?E\.?|Bachelor of Engineering)\b", "Bachelor's", "B.E.", "Engineering"),
    (r"\b(B\.?S\.?|Bachelor of Science|B\.?Sc)\b", "Bachelor's", "B.Sc", "Computer Science"),
    (r"\b(B\.?C\.?A|Bachelor of Computer Applications)\b", "Bachelor's", "BCA", "Computer Applications"),
    (r"\b(B\.?B\.?A|Bachelor of Business Administration)\b", "Bachelor's", "BBA", "Business Administration"),
    (r"\b(B\.?Com|Bachelor of Commerce)\b", "Bachelor's", "B.Com", "Commerce"),
    (r"\b(B\.?A|Bachelor of Arts)\b", "Bachelor's", "B.A.", "Other"),
    (r"\b(Diploma|Polytechnic)\b", "Diploma", "Diploma", "Engineering"),
]

KNOWN_UNIVERSITIES = [
    "Mahatma Gandhi University", "MG University", "University of Kerala",
    "Calicut University", "Kannur University", "APJ Abdul Kalam Technological University",
    "KTU", "Anna University", "Visvesvaraya Technological University", "VTU",
    "Bangalore University", "University of Madras", "Delhi University", "DU",
    "Mumbai University", "Pune University", "Osmania University", "JNTU",
    "Jawaharlal Nehru Technological University"
]


def extract_text_from_docx(file_obj) -> str:
    """Extract text from a .docx file including paragraphs and tables."""
    try:
        if hasattr(file_obj, "read"):
            content = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            file_stream = io.BytesIO(content)
        elif isinstance(file_obj, (bytes, bytearray)):
            file_stream = io.BytesIO(file_obj)
        else:
            with open(file_obj, "rb") as f:
                file_stream = io.BytesIO(f.read())

        with zipfile.ZipFile(file_stream) as docx:
            xml_content = docx.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            
            paragraphs = []
            for p in tree.findall(".//w:p", ns):
                texts = [node.text for node in p.findall(".//w:t", ns) if node.text]
                p_text = "".join(texts).strip()
                if p_text:
                    paragraphs.append(p_text)
            return "\n".join(paragraphs)
    except Exception:
        return ""


def _parse_cmap(cmap_bytes: bytes) -> Dict[int, str]:
    """Parse Adobe ToUnicode CMap streams (beginbfchar and beginbfrange)."""
    cmap = {}
    bfchar_blocks = re.findall(rb'beginbfchar(.*?)endbfchar', cmap_bytes, re.DOTALL)
    for block in bfchar_blocks:
        pairs = re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>', block)
        for src, dst in pairs:
            try:
                src_code = int(src, 16)
                dst_char = chr(int(dst, 16))
                cmap[src_code] = dst_char
            except Exception:
                pass
    bfrange_blocks = re.findall(rb'beginbfrange(.*?)endbfrange', cmap_bytes, re.DOTALL)
    for block in bfrange_blocks:
        ranges = re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>', block)
        for s_start, s_end, d_start in ranges:
            try:
                start_c = int(s_start, 16)
                end_c = int(s_end, 16)
                dst_c = int(d_start, 16)
                for code in range(start_c, end_c + 1):
                    cmap[code] = chr(dst_c + (code - start_c))
            except Exception:
                pass
        arr_ranges = re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*\[(.*?)\]', block, re.DOTALL)
        for s_start, s_end, dst_list_str in arr_ranges:
            try:
                start_c = int(s_start, 16)
                dst_hexes = re.findall(rb'<([0-9a-fA-F]+)>', dst_list_str)
                for idx, d_hex in enumerate(dst_hexes):
                    code = start_c + idx
                    cmap[code] = chr(int(d_hex, 16))
            except Exception:
                pass
    return cmap


def _extract_pdf_literal_string(data: bytes, pos: int) -> Tuple[bytes, int]:
    """Extract a single PDF literal parenthesized string with nested/escaped parens starting at pos."""
    if pos >= len(data) or data[pos:pos+1] != b'(':
        return b'', pos
    depth = 0
    res = bytearray()
    i = pos
    while i < len(data):
        c = data[i:i+1]
        if c == b'\\' and i + 1 < len(data):
            next_c = data[i+1:i+2]
            if next_c in (b'(', b')', b'\\'):
                res.append(next_c[0])
                i += 2
                continue
            elif next_c == b'n':
                res.append(ord('\n'))
                i += 2
                continue
            elif next_c == b'r':
                res.append(ord('\r'))
                i += 2
                continue
            elif next_c == b't':
                res.append(ord('\t'))
                i += 2
                continue
            elif next_c in b'01234567':
                oct_b = next_c
                i += 2
                while len(oct_b) < 3 and i < len(data) and data[i:i+1] in b'01234567':
                    oct_b += data[i:i+1]
                    i += 1
                res.append(int(oct_b, 8))
                continue
            else:
                res.append(next_c[0])
                i += 2
                continue
        elif c == b'(':
            depth += 1
            if depth > 1:
                res.append(ord('('))
        elif c == b')':
            depth -= 1
            if depth == 0:
                i += 1
                break
            else:
                res.append(ord(')'))
        else:
            res.append(c[0])
        i += 1
    return bytes(res), i


def _decode_cid_string(b_str: bytes, cmap: Dict[int, str], fallback_cmap: Dict[int, str]) -> str:
    """Decode raw bytes using 2-byte or 1-byte CID mappings."""
    out = []
    i = 0
    while i < len(b_str):
        if i + 1 < len(b_str):
            cid2 = (b_str[i] << 8) | b_str[i+1]
            if cid2 in cmap:
                out.append(cmap[cid2])
                i += 2
                continue
            elif cid2 in fallback_cmap:
                out.append(fallback_cmap[cid2])
                i += 2
                continue
        cid1 = b_str[i]
        if cid1 in cmap:
            out.append(cmap[cid1])
        elif cid1 in fallback_cmap:
            out.append(fallback_cmap[cid1])
        elif 32 <= cid1 <= 126:
            out.append(chr(cid1))
        i += 1
    return ''.join(out)


def extract_text_from_pdf(file_obj) -> str:
    """
    Extracts text from PDF files using pure python with full CMap and Identity-H font support.
    Supports single-byte and multi-byte CID fonts, FlateDecode decompression, and positioning operators.
    """
    try:
        if hasattr(file_obj, "read"):
            data = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
        elif isinstance(file_obj, (bytes, bytearray)):
            data = bytes(file_obj)
        else:
            with open(file_obj, "rb") as f:
                data = f.read()

        obj_streams = {}
        for m in re.finditer(rb'(\d+)\s+\d+\s+obj\s*<<(?:(?!endobj).)*?>>\s*stream[\r\n]+(.*?)[\r\n]+endstream', data, re.DOTALL):
            oid = int(m.group(1))
            raw_s = m.group(2)
            try:
                obj_streams[oid] = zlib.decompress(raw_s)
            except Exception:
                obj_streams[oid] = raw_s

        # Map Font IDs to ToUnicode IDs
        font_id_to_tounicode = {}
        for m in re.finditer(rb'(\d+)\s+\d+\s+obj\s*<<(?:(?!endobj).)*?/Type\s*/Font\b(?:(?!endobj).)*?/ToUnicode\s+(\d+)\s+\d+\s+R(?:(?!endobj).)*?>>\s*endobj', data, re.DOTALL):
            font_id_to_tounicode[int(m.group(1))] = int(m.group(2))

        # Map font names in resource dictionaries
        font_name_to_tounicode = {}
        for m in re.finditer(rb'/([A-Za-z0-9_]+)\s+(\d+)\s+\d+\s+R', data):
            fn = '/' + m.group(1).decode()
            fid = int(m.group(2))
            if fid in font_id_to_tounicode:
                tu_id = font_id_to_tounicode[fid]
                if tu_id in obj_streams:
                    font_name_to_tounicode[fn] = _parse_cmap(obj_streams[tu_id])

        fallback_cmap = {}
        for cm in font_name_to_tounicode.values():
            fallback_cmap.update(cm)
        if not fallback_cmap:
            for oid, stream in obj_streams.items():
                if b'begincmap' in stream:
                    fallback_cmap.update(_parse_cmap(stream))

        all_text_lines = []
        for oid, stream_bytes in obj_streams.items():
            if b'BT' not in stream_bytes:
                continue
            i = 0
            cur_font = '/F4'
            cur_line = []
            while i < len(stream_bytes):
                if stream_bytes[i:i+1] == b'/':
                    font_m = re.match(rb'/([A-Za-z0-9_]+)\s+[0-9\.]+\s+Tf', stream_bytes[i:])
                    if font_m:
                        cur_font = '/' + font_m.group(1).decode()
                        i += font_m.end()
                        continue
                td_m = re.match(rb'([0-9\.\-]+)\s+([0-9\.\-]+)\s+Td', stream_bytes[i:])
                if td_m:
                    dy = float(td_m.group(2))
                    if dy != 0 and cur_line:
                        all_text_lines.append(''.join(cur_line))
                        cur_line = []
                    i += td_m.end()
                    continue
                tm_m = re.match(rb'[0-9\.\-]+\s+[0-9\.\-]+\s+[0-9\.\-]+\s+[0-9\.\-]+\s+[0-9\.\-]+\s+([0-9\.\-]+)\s+Tm', stream_bytes[i:])
                if tm_m:
                    if cur_line:
                        all_text_lines.append(''.join(cur_line))
                        cur_line = []
                    i += tm_m.end()
                    continue
                if stream_bytes[i:i+2] == b'T*':
                    if cur_line:
                        all_text_lines.append(''.join(cur_line))
                        cur_line = []
                    i += 2
                    continue
                if stream_bytes[i:i+1] == b'(':
                    raw_str, end_pos = _extract_pdf_literal_string(stream_bytes, i)
                    tj_match = re.match(rb'\s*Tj', stream_bytes[end_pos:])
                    if tj_match:
                        cm = font_name_to_tounicode.get(cur_font, fallback_cmap)
                        cur_line.append(_decode_cid_string(raw_str, cm, fallback_cmap))
                        i = end_pos + tj_match.end()
                        continue
                    else:
                        i += 1
                        continue
                if stream_bytes[i:i+1] == b'<':
                    hex_m = re.match(rb'<([0-9a-fA-F\s]+)>\s*Tj', stream_bytes[i:])
                    if hex_m:
                        h_str = re.sub(rb'\s+', b'', hex_m.group(1))
                        try:
                            raw_str = bytes.fromhex(h_str.decode())
                            cm = font_name_to_tounicode.get(cur_font, fallback_cmap)
                            cur_line.append(_decode_cid_string(raw_str, cm, fallback_cmap))
                        except Exception:
                            pass
                        i += hex_m.end()
                        continue
                if stream_bytes[i:i+1] == b'[':
                    tj_arr_end = stream_bytes.find(b']', i)
                    if tj_arr_end != -1:
                        after_bracket = stream_bytes[tj_arr_end+1:tj_arr_end+10]
                        if b'TJ' in after_bracket:
                            arr_content = stream_bytes[i+1:tj_arr_end]
                            sub_i = 0
                            cm = font_name_to_tounicode.get(cur_font, fallback_cmap)
                            while sub_i < len(arr_content):
                                if arr_content[sub_i:sub_i+1] == b'(':
                                    sub_raw, sub_end = _extract_pdf_literal_string(arr_content, sub_i)
                                    cur_line.append(_decode_cid_string(sub_raw, cm, fallback_cmap))
                                    sub_i = sub_end
                                else:
                                    sub_i += 1
                            i = tj_arr_end + after_bracket.find(b'TJ') + 2
                            continue
                i += 1
            if cur_line:
                all_text_lines.append(''.join(cur_line))

        cleaned = []
        for line in all_text_lines:
            line_str = re.sub(r'[ \t]+', ' ', line).strip()
            if line_str:
                cleaned.append(line_str)
        if cleaned:
            return '\n'.join(cleaned)
    except Exception:
        pass

    ascii_strings = re.findall(rb"[a-zA-Z0-9@\.\,\:\-\+\(\)\s]{4,}", data)
    return "\n".join([s.decode("latin-1", errors="ignore").strip() for s in ascii_strings if len(s.strip()) > 3])


def extract_text(file_obj, filename: str = "") -> str:
    """Extract plain text based on file type."""
    fname = (filename or getattr(file_obj, "name", "") or "").lower()
    if fname.endswith(".docx"):
        return extract_text_from_docx(file_obj)
    elif fname.endswith(".pdf"):
        return extract_text_from_pdf(file_obj)
    else:
        try:
            if hasattr(file_obj, "read"):
                raw = file_obj.read()
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
            elif isinstance(file_obj, (bytes, bytearray)):
                raw = file_obj
            else:
                with open(file_obj, "rb") as f:
                    raw = f.read()
            
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def parse_resume(file_obj, filename: str = "") -> Dict[str, Any]:
    """
    Parses resume text and extracts structured candidate data:
    - First Name, Middle Name, Last Name
    - Email, Phone, Address, State, Country
    - 10th Education: Board, School, Percentage, Passing Year
    - 12th Education: Board, School, Stream, Percentage, Passing Year
    - Higher Education: Level, Degree, Field of Study, Institution, University, Status, Passing Year, CGPA/Percentage
    - Experience: is_fresher, total_experience_years, total_experience_months, current_organization, current_designation
    - Skills: Extracted skills list
    """
    raw_text = extract_text(file_obj, filename)
    
    result = {
        # Personal Information
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "email": "",
        "phone": "",
        "address": "",
        "state": "",
        "country": "India",
        
        # 10th Education
        "tenth_board": "",
        "tenth_school": "",
        "tenth_percentage": "",
        "tenth_passing_year": None,
        
        # 12th Education
        "twelfth_board": "",
        "twelfth_school": "",
        "twelfth_stream": "",
        "twelfth_percentage": "",
        "twelfth_passing_year": None,
        
        # Higher Education (Primary)
        "education_level": "",
        "degree_program": "",
        "field_of_study": "Computer Applications",
        "institution": "",
        "university_board": "",
        "education_status": "Graduated",
        "completion_year": None,
        "percentage_or_cgpa": "",
        
        # List of all extracted higher education records
        "higher_educations": [],
        
        # Experience
        "is_fresher": "Yes",
        "total_experience_years": 0,
        "total_experience_months": 0,
        "current_organization": "",
        "current_designation": "",
        
        # Skills
        "skills": "",
        "raw_text": raw_text[:2000],
    }

    if not raw_text:
        return result

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    full_text = "\n".join(lines)
    full_text_lower = full_text.lower()

    # 1. EMAIL EXTRACTION
    direct_email_match = re.search(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", full_text)
    if direct_email_match:
        matched_email = direct_email_match.group(0).lower().strip()
        local_part = matched_email.split("@")[0]
        # If the local part is only numbers (e.g. 2003@gmail.com), check if username was split across line
        if local_part.isdigit() or len(local_part) <= 4:
            prev_m = re.search(r"(?:^|\n)[\|\-\•\*\s]*([a-zA-Z0-9_.+-]{3,})\s*\n\s*" + re.escape(direct_email_match.group(0)), full_text, re.I)
            if prev_m:
                cand_user = prev_m.group(1).strip()
                result["email"] = (cand_user + matched_email).lower()
        if not result["email"]:
            result["email"] = matched_email

    # 2. PHONE NUMBER EXTRACTION
    phone_match = re.search(r"(?:\+?91[-.\s]?)?[6-9]\d{9}\b", full_text)
    if not phone_match:
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", full_text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

    # 3. NAME EXTRACTION
    name_found = False
    name_label_match = re.search(r"(?:name|candidate name|full name)\s*[:\-]\s*([a-zA-Z\s\.]{2,40})", full_text, re.IGNORECASE)
    if name_label_match:
        words = name_label_match.group(1).strip().split()
        if 1 <= len(words) <= 4:
            result["first_name"] = words[0]
            if len(words) == 2:
                result["last_name"] = words[1]
            elif len(words) == 3:
                result["middle_name"] = words[1]
                result["last_name"] = words[2]
            elif len(words) >= 4:
                result["middle_name"] = " ".join(words[1:-1])
                result["last_name"] = words[-1]
            name_found = True

    if not name_found:
        # Search lines for Title Cased candidate name (e.g. "Binitta Saji", "John Doe")
        # Ignore single lowercase username handles, header labels, contacts
        candidates_found = []
        for line in lines[:15]:
            clean_l = re.sub(r'^[\|\-\•\*\s]+', '', line).strip()
            if not clean_l or len(clean_l) > 40:
                continue
            if "@" in clean_l or "resume" in clean_l.lower() or "curriculum" in clean_l.lower():
                continue
            if any(st.lower() in clean_l.lower() for st in INDIAN_STATES) or any(c.isdigit() for c in clean_l):
                continue
            if "linkedin" in clean_l.lower() or "github" in clean_l.lower() or "http" in clean_l.lower() or "/" in clean_l:
                continue
            if any(k in clean_l.lower() for k in ["summary", "skills", "experience", "education", "student", "engineer", "developer"]):
                continue

            words = clean_l.split()
            # Multi-word proper name (e.g. Binitta Saji, John Alexander Doe)
            if 2 <= len(words) <= 4 and all(w.replace(".", "").isalpha() and w[0].isupper() for w in words):
                candidates_found.append((2, words))
            # Single word fallback only if capitalized and not a single lower-case word
            elif len(words) == 1 and words[0].isalpha() and words[0][0].isupper() and len(words[0]) > 2:
                candidates_found.append((1, words))

        if candidates_found:
            # Pick the best candidate (multi-word preferred)
            candidates_found.sort(key=lambda x: x[0], reverse=True)
            words = candidates_found[0][1]
            result["first_name"] = words[0]
            if len(words) == 2:
                result["last_name"] = words[1]
            elif len(words) == 3:
                result["middle_name"] = words[1]
                result["last_name"] = words[2]
            elif len(words) >= 4:
                result["middle_name"] = " ".join(words[1:-1])
                result["last_name"] = words[-1]
            name_found = True

    # Fallback if no multi-word capitalized name was found
    if not name_found:
        for line in lines[:6]:
            clean_l = re.sub(r'^[\|\-\•\*\s]+', '', line).strip()
            words = clean_l.split()
            if 1 <= len(words) <= 3 and all(w.replace(".", "").isalpha() for w in words):
                result["first_name"] = words[0].capitalize()
                if len(words) >= 2:
                    result["last_name"] = words[1].capitalize()
                break

    # 4. LOCATION / STATE / COUNTRY EXTRACTION
    for st in INDIAN_STATES:
        if re.search(r"\b" + re.escape(st) + r"\b", full_text, re.IGNORECASE):
            result["state"] = st
            break

    addr_match = re.search(r"(?:address|residence|location)\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+){0,2})", full_text, re.IGNORECASE)
    if addr_match:
        result["address"] = addr_match.group(1).strip()
    elif result["state"]:
        loc_lines = [l for l in lines[:5] if result["state"].lower() in l.lower()]
        if loc_lines:
            result["address"] = loc_lines[0].replace("|", "").strip()

    # 5. SKILLS EXTRACTION
    extracted_skills = []
    skills_sec_match = re.search(
        r"(?:technical skills|key skills|skills|core competencies|technologies|tools & technologies|programming|frameworks|database management|tools)\s*[:\-\n]+([^\n\r]+(?:\n[^\n\r]+){0,8})",
        full_text,
        re.IGNORECASE
    )
    if skills_sec_match:
        sec_content = skills_sec_match.group(1).strip()
        raw_items = re.split(r"[,;•|/·\n\r:]+", sec_content)
        for item in raw_items:
            clean_item = item.strip()
            if clean_item and 1 < len(clean_item) < 30:
                if clean_item.lower() not in SKILL_HEADER_WORDS:
                    if not any(clean_item.lower() == s.lower() for s in extracted_skills):
                        extracted_skills.append(clean_item)

    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, full_text_lower):
            if not any(skill.lower() == s.lower() for s in extracted_skills):
                extracted_skills.append(skill)

    if extracted_skills:
        result["skills"] = ", ".join(extracted_skills[:15])

    # Helper function for percentage / marks
    def find_pct(text_block: str) -> str:
        m1 = re.search(r"(?:percentage|cgpa|ccpa|marks|score|aggregate)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)\s*%?", text_block, re.I)
        if m1:
            return f"{m1.group(1)}%"
        m2 = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%", text_block)
        if m2:
            return f"{m2.group(1)}%"
        return ""

    # 6. 10th STANDARD EDUCATION EXTRACTION
    tenth_match = None
    for i, line in enumerate(lines):
        if re.search(r"\b(10th|sslc|matriculation|secondary school|class x\b|x\s*\([^\)]*\))", line, re.I) and not re.search(r"\b(class xii|higher secondary|12th)\b", line, re.I):
            tenth_block = "\n".join(lines[i:min(len(lines), i + 4)])
            tenth_match = tenth_block
            break

    if tenth_match:
        if re.search(r"\bCBSE\b", tenth_match, re.I):
            result["tenth_board"] = "CBSE"
        elif re.search(r"\bICSE\b", tenth_match, re.I):
            result["tenth_board"] = "ICSE"
        else:
            result["tenth_board"] = "State Board"

        for l in tenth_match.splitlines():
            if any(w in l.lower() for w in ["school", "vidyalaya", "academy", "matha"]) and not re.search(r"\b(higher secondary|12th)\b", l, re.I):
                clean_sch = re.sub(r'^(?:10th|x\s*\([^\)]*\))\s*', '', l, flags=re.I).strip()
                result["tenth_school"] = clean_sch
                break

        result["tenth_percentage"] = find_pct(tenth_match)

        t_yr = re.search(r"\b(199\d|20[0-2]\d)\b", tenth_match)
        if t_yr:
            result["tenth_passing_year"] = int(t_yr.group(1))

    # 7. 12th STANDARD EDUCATION EXTRACTION
    twelfth_match = None
    for i, line in enumerate(lines):
        if re.search(r"\b(12th|twelfth|hsc|higher secondary|intermediate|plus two|\+2|class xii)\b", line, re.I):
            sub_lines = []
            for sl in lines[i:min(len(lines), i + 4)]:
                if any(k in sl.lower() for k in ["bachelor", "master", "degree", "b.tech", "bca", "mca", "academics", "certification"]):
                    break
                sub_lines.append(sl)
            twelfth_match = "\n".join(sub_lines) if sub_lines else line
            break

    if twelfth_match:
        if re.search(r"\bCBSE\b", twelfth_match, re.I):
            result["twelfth_board"] = "CBSE"
        elif re.search(r"\bISC\b", twelfth_match, re.I):
            result["twelfth_board"] = "ISC"
        else:
            result["twelfth_board"] = "State Board"

        if re.search(r"\b(computer science|cs)\b", twelfth_match, re.I):
            result["twelfth_stream"] = "Computer Science"
        elif re.search(r"\b(science|pcm|pcb)\b", twelfth_match, re.I):
            result["twelfth_stream"] = "Science"
        elif re.search(r"\b(commerce)\b", twelfth_match, re.I):
            result["twelfth_stream"] = "Commerce"
        elif re.search(r"\b(arts|humanities)\b", twelfth_match, re.I):
            result["twelfth_stream"] = "Humanities"
        else:
            result["twelfth_stream"] = "Science"

        for l in twelfth_match.splitlines():
            if any(w in l.lower() for w in ["school", "college", "govt", "vidyalaya"]):
                if not any(w in l.lower() for w in ["class xii", "education (", "higher secondary education"]):
                    result["twelfth_school"] = l.strip()
                    break

        result["twelfth_percentage"] = find_pct(twelfth_match)

        tw_yrs = re.findall(r"\b(199\d|20[0-2]\d)\b", twelfth_match)
        if tw_yrs:
            result["twelfth_passing_year"] = int(tw_yrs[-1])

    # 8. HIGHER EDUCATION EXTRACTION
    higher_ed_list = []
    seen_programs = set()

    # Search for global university in text
    detected_univ = ""
    for u in KNOWN_UNIVERSITIES:
        if re.search(r"\b" + re.escape(u) + r"\b", full_text, re.IGNORECASE):
            detected_univ = u
            break
    if not detected_univ:
        univ_match = re.search(r"([A-Za-z\s]+(?:University|Institute of Technology|Deemed University))", full_text, re.I)
        if univ_match:
            detected_univ = univ_match.group(1).strip()

    for idx, line in enumerate(lines):
        for pat, edu_lvl, prog_name, field_name in DEGREE_MAPPINGS:
            if re.search(pat, line, re.I):
                snippet_lines = lines[idx:min(len(lines), idx + 4)]
                snippet_text = "\n".join(snippet_lines)

                edu_yr = None
                yr_range_match = re.search(r"\b(20[1-3]\d)\s*[-–]\s*(20[1-3]\d)\b", snippet_text)
                if yr_range_match:
                    edu_yr = int(yr_range_match.group(2))
                else:
                    yr_matches = re.findall(r"\b(20[1-3]\d)\b", snippet_text)
                    if yr_matches:
                        edu_yr = int(yr_matches[-1])

                edu_score = ""
                score_match = re.search(r"(?:ccpa|cgpa|gpa|percentage|%)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)", snippet_text, re.I)
                if score_match:
                    edu_score = score_match.group(1).strip()

                inst_name = ""
                univ_name = detected_univ
                for sl in snippet_lines:
                    if any(w in sl.lower() for w in ["college", "university", "institute", "campus", "academy"]) and not any(w in sl.lower() for w in ["bachelor", "master", "degree", "bca", "mca", "b.tech", "higher secondary"]):
                        inst_name = sl.strip()
                        break

                # Infer university if known college
                if not univ_name:
                    if "cherpunkal" in inst_name.lower() or "bvm" in inst_name.lower():
                        univ_name = "Mahatma Gandhi University"
                    elif "kerala" in result["state"].lower():
                        univ_name = "Mahatma Gandhi University"
                    else:
                        univ_name = "Affiliated University"

                rec_key = f"{edu_lvl}_{prog_name}"
                record = {
                    "education_level": edu_lvl,
                    "degree_program": prog_name,
                    "field_of_study": field_name,
                    "institution": inst_name or "College / Institute",
                    "university_board": univ_name,
                    "education_status": "Graduated",
                    "completion_year": edu_yr,
                    "percentage_or_cgpa": edu_score,
                }
                if rec_key not in seen_programs or (inst_name and inst_name != "College / Institute"):
                    if rec_key in seen_programs:
                        for h_idx, r in enumerate(higher_ed_list):
                            if r["degree_program"] == prog_name:
                                higher_ed_list[h_idx] = record
                    else:
                        seen_programs.add(rec_key)
                        higher_ed_list.append(record)

    higher_ed_list.sort(key=lambda r: (1 if r["institution"] != "College / Institute" else 0, 1 if r["percentage_or_cgpa"] else 0), reverse=True)

    if higher_ed_list:
        result["higher_educations"] = higher_ed_list
        primary_edu = higher_ed_list[0]
        result["education_level"] = primary_edu["education_level"]
        result["degree_program"] = primary_edu["degree_program"]
        result["field_of_study"] = primary_edu["field_of_study"]
        result["institution"] = primary_edu["institution"]
        result["university_board"] = primary_edu["university_board"]
        result["completion_year"] = primary_edu["completion_year"]
        result["percentage_or_cgpa"] = primary_edu["percentage_or_cgpa"]

    # 9. WORK EXPERIENCE EXTRACTION
    exp_matches = re.findall(r"(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s*(?:of)?\s*experience)?", full_text, re.IGNORECASE)
    if exp_matches:
        try:
            years_float = float(exp_matches[0])
            years = int(years_float)
            months = int(round((years_float - years) * 12))
            if years > 0 or months > 0:
                result["is_fresher"] = "No"
                result["total_experience_years"] = years
                result["total_experience_months"] = months
        except ValueError:
            pass
    elif re.search(r"\b(fresher|no prior experience|entry level)\b", full_text, re.IGNORECASE):
        result["is_fresher"] = "Yes"
        result["total_experience_years"] = 0
        result["total_experience_months"] = 0

    internship_match = re.search(r"(?:internship|intern)\s+(?:at|in)\s+([a-zA-Z0-9\s\.\&]{3,40})", full_text, re.IGNORECASE)
    if internship_match:
        result["current_organization"] = re.sub(r'\s+', ' ', internship_match.group(1)).strip()
        result["current_designation"] = "Intern"

    return result
