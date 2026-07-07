import re
from fastapi import HTTPException, status

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Simple blacklist of disposable/suspicious email domains
EMAIL_DOMAIN_BLACKLIST = {
    "mailinator.com",
    "tempmail.com",
    "sharklasers.com",
    "guerrillamail.com",
    "10minutemail.com"
}

def validate_email(email: str) -> str:
    """
    Validates email format and checks against disposable email blacklists.
    """
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email field cannot be empty."
        )
    
    email = email.strip().lower()
    
    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )
    
    parts = email.split("@")
    if len(parts) == 2:
        domain = parts[1]
        if domain in EMAIL_DOMAIN_BLACKLIST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disposable email domains are not allowed."
            )
            
    return email

def validate_password(password: str) -> str:
    """
    Validates that password matches minimum security rules:
    - Min 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one numeric digit
    - At least one special character
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password field cannot be empty."
        )
        
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
        
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter."
        )
        
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter."
        )
        
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one numeric digit."
        )
        
    # Check for special character
    special_chars = re.compile(r"[@$!%*?&#^()_+=\-\[\]{}|\\:;\"'<>,./?]")
    if not special_chars.search(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character (e.g. @$!%*?&)."
        )
        
    return password

def validate_full_name(name: str) -> str:
    """
    Validates that name is not empty and fits standard limits.
    """
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name field cannot be empty."
        )
        
    name = name.strip()
    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at least 2 characters long."
        )
        
    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot exceed 100 characters."
        )
        
    return name

def validate_course_title(title: str) -> str:
    """
    Validates that a course title is not empty and is under 200 characters.
    """
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course title cannot be empty."
        )
    title = title.strip()
    if len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course title cannot exceed 200 characters."
        )
    return title

def validate_category(category: str) -> str:
    """
    Validates that a course category is not empty and under 100 characters.
    """
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be empty."
        )
    category = category.strip()
    if len(category) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot exceed 100 characters."
        )
    return category

def validate_level(level: str) -> str:
    """
    Validates that a level is one of the allowed enums.
    """
    level = level.strip().lower()
    if level not in ["beginner", "intermediate", "advanced"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Level must be one of: beginner, intermediate, advanced."
        )
    return level

def validate_quiz_question(question_text: str) -> str:
    if not question_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question text cannot be empty.")
    question_text = question_text.strip()
    if len(question_text) > 5000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question text cannot exceed 5000 characters.")
    return question_text

def validate_quiz_options(options: list) -> list:
    if not options or len(options) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quizzes must contain at least 2 options.")
    return options

def validate_note_content(content: str) -> str:
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note content cannot be empty.")
    if len(content) > 100000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note content cannot exceed 100,000 characters.")
    return content

def validate_message(message: str) -> str:
    if not message or not message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")
    if len(message) > 10000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot exceed 10,000 characters.")
    return message

def validate_audio_file(file) -> None:
    # Check size < 50MB (52,428,800 bytes)
    # file can be FastAPI UploadFile
    filename = getattr(file, "filename", "") or ""
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""
    if file_ext not in ["mp3", "wav", "m4a"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio format. Allowed: mp3, wav, m4a.")
    
    # UploadFile size checking might require reading/checking size parameter if available
    # Or checking during file writing. Since we check upload, we will validate.
    # If size is present in metadata
    size = getattr(file, "size", None)
    if size and size > 52428800:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file size cannot exceed 50MB.")

def validate_learning_style(style: str) -> str:
    style = style.strip().lower()
    if style not in ["visual", "auditory", "kinesthetic", "mixed"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Learning style must be visual, auditory, kinesthetic, or mixed.")
    return style

def validate_learning_pace(pace: str) -> str:
    pace = pace.strip().lower()
    if pace not in ["slow", "normal", "fast"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Learning pace must be slow, normal, or fast.")
    return pace

def validate_role(role: str) -> str:
    role = role.strip().lower()
    if role not in ["student", "tutor", "admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be student, tutor, or admin.")
    return role

