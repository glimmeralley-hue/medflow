"""User profile data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    """Represents user profile information."""
    
    id: int = 1  # Always 1 for single-user application
    name: Optional[str] = None
    school: Optional[str] = None
    year_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    ambitions: Optional[str] = None
    specialties: Optional[str] = None
    hobbies: Optional[str] = None
    study_plan: Optional[str] = None
    motivation: Optional[str] = None
    profile_picture_path: Optional[str] = None
    music_file_path: Optional[str] = None
    music_folder_path: Optional[str] = None
    updated_at: Optional[str] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if profile has essential information."""
        return bool(self.name and self.school and self.year_of_study)
    
    @property
    def display_name(self) -> str:
        """Get display name, falling back to default."""
        return self.name if self.name else "Medical Student"
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'school': self.school,
            'year_of_study': self.year_of_study,
            'graduation_year': self.graduation_year,
            'ambitions': self.ambitions,
            'specialties': self.specialties,
            'hobbies': self.hobbies,
            'study_plan': self.study_plan,
            'motivation': self.motivation,
            'profile_picture': self.profile_picture_path,
            'music_file': self.music_file_path,
            'music_folder': self.music_folder_path,
            'updated_at': self.updated_at,
            'is_complete': self.is_complete,
            'display_name': self.display_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """Create profile from dictionary."""
        return cls(
            id=data.get('id', 1),
            name=data.get('name'),
            school=data.get('school'),
            year_of_study=data.get('year_of_study'),
            graduation_year=data.get('graduation_year'),
            ambitions=data.get('ambitions'),
            specialties=data.get('specialties'),
            hobbies=data.get('hobbies'),
            study_plan=data.get('study_plan'),
            motivation=data.get('motivation'),
            profile_picture_path=data.get('profile_picture_path'),
            music_file_path=data.get('music_file_path'),
            music_folder_path=data.get('music_folder_path'),
            updated_at=data.get('updated_at')
        )
