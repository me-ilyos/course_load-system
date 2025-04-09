from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.departments.models import Department, Professor
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates dummy data for departments, department heads, and professors'

    def __init__(self):
        super().__init__()
        # List of Marvel and DC heroes with their full names
        self.hero_names = [
            # Marvel Heroes
            "Tony Stark",           # Iron Man
            "Steve Rogers",         # Captain America
            "Bruce Banner",        # Hulk
            "Thor Odinson",        # Thor
            "Natasha Romanoff",    # Black Widow
            "Clint Barton",        # Hawkeye
            "Peter Parker",        # Spider-Man
            "Stephen Strange",     # Doctor Strange
            "T'Challa",           # Black Panther
            "Carol Danvers",       # Captain Marvel
            "Scott Lang",          # Ant-Man
            "Wanda Maximoff",      # Scarlet Witch
            "Vision",              # Vision
            "Sam Wilson",          # Falcon
            "James Rhodes",        # War Machine
            "Bucky Barnes",        # Winter Soldier
            "Peter Quill",         # Star-Lord
            "Matt Murdock",        # Daredevil
            "Reed Richards",       # Mr. Fantastic
            "Susan Storm",         # Invisible Woman
            "Johnny Storm",        # Human Torch
            "Ben Grimm",          # The Thing
            "Charles Xavier",      # Professor X
            "Jean Grey",          # Phoenix
            "Scott Summers",      # Cyclops
            "Ororo Munroe",       # Storm
            "Logan Howlett",      # Wolverine
            "Hank McCoy",         # Beast
            "Warren Worthington", # Angel
            "Bobby Drake",        # Iceman
            # DC Heroes
            "Bruce Wayne",        # Batman
            "Clark Kent",         # Superman
            "Diana Prince",       # Wonder Woman
            "Barry Allen",        # The Flash
            "Hal Jordan",         # Green Lantern
            "Arthur Curry",       # Aquaman
            "Oliver Queen",       # Green Arrow
            "Dick Grayson",       # Nightwing
            "Victor Stone",       # Cyborg
            "John Stewart",       # Green Lantern
            "Dinah Lance",        # Black Canary
            "Kara Danvers",       # Supergirl
            "John Constantine",   # Constantine
            "Zatanna Zatara",    # Zatanna
            "Ray Palmer",         # The Atom
            "Carter Hall",        # Hawkman
            "Shiera Hall",        # Hawkgirl
            "Billy Batson",       # Shazam
            "Kent Nelson",        # Doctor Fate
            "Michael Carter",     # Booster Gold
        ]
        random.shuffle(self.hero_names)  # Shuffle the names for random distribution
        self.name_index = 0
        self.DEFAULT_PASSWORD = "103203303A"
        self.used_usernames = set()  # Track used usernames

    def _get_next_name(self):
        if self.name_index >= len(self.hero_names):
            raise ValueError("Ran out of unique names! Add more hero names to the list.")
        name = self.hero_names[self.name_index]
        self.name_index += 1
        return name

    def _create_unique_username(self, full_name):
        # Convert to lowercase and replace spaces with dots
        username = full_name.lower().replace(' ', '.')
        # Remove any special characters (like apostrophes in names like T'Challa)
        username = ''.join(c for c in username if c.isalnum() or c == '.')
        
        if username in self.used_usernames:
            raise ValueError(f"Duplicate username found: {username}. This should not happen with our expanded hero list!")
        
        self.used_usernames.add(username)
        return username

    def _create_department_head(self, department_code):
        full_name = self._get_next_name()
        first_name, last_name = full_name.split(maxsplit=1) if " " in full_name else (full_name, "")
        username = self._create_unique_username(full_name)
        
        user = User.objects.create_user(
            username=username,
            password=self.DEFAULT_PASSWORD,
            email=f"{username}@namdtu.edu",
            first_name=first_name,
            last_name=last_name,
            user_type=User.UserType.DEPARTMENT_HEAD
        )
        return user

    def _create_professor(self, department, index):
        full_name = self._get_next_name()
        first_name, last_name = full_name.split(maxsplit=1) if " " in full_name else (full_name, "")
        username = self._create_unique_username(full_name)
        
        user = User.objects.create_user(
            username=username,
            password=self.DEFAULT_PASSWORD,
            email=f"{username}@namdtu.edu",
            first_name=first_name,
            last_name=last_name,
            user_type=User.UserType.PROFESSOR
        )

        experience_years = random.randint(0, 10)
        has_phd = random.choice([True, False])

        professor = Professor.objects.create(
            user=user,
            department=department,
            full_name=full_name,
            email=f"{username}@namdtu.edu",
            phone_number=f"+1-555-{random.randint(1000000, 9999999)}",
            years_of_experience=experience_years,
            has_phd=has_phd
        )
        return professor

    def handle(self, *args, **kwargs):
        # Clean existing data
        self.stdout.write('Cleaning existing data...')
        Professor.objects.all().delete()
        Department.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # Keep superuser accounts

        # Create departments with their heads
        departments_data = [
            {
                'code': 'CS',
                'title': 'Computer Science',
                'description': 'Department of Computer Science and Software Engineering'
            },
            {
                'code': 'MATH',
                'title': 'Mathematics',
                'description': 'Department of Mathematics and Statistics'
            },
            {
                'code': 'PHYS',
                'title': 'Physics',
                'description': 'Department of Physics and Astronomy'
            },
            {
                'code': 'ENG',
                'title': 'Engineering',
                'description': 'Department of Engineering Sciences'
            }
        ]

        self.stdout.write('Creating departments and department heads...')
        
        for dept_data in departments_data:
            # Create department
            department = Department.objects.create(**dept_data)
            
            # Create and assign department head
            head = self._create_department_head(department.code)
            department.head = head
            department.save()
            
            # Create 7-10 professors for each department
            num_professors = random.randint(7, 10)
            self.stdout.write(f'Creating {num_professors} professors for {department.code}...')
            
            for i in range(num_professors):
                self._create_professor(department, i + 1)

        # Print summary
        self.stdout.write(self.style.SUCCESS('Successfully created dummy data:'))
        self.stdout.write(f'- Departments: {Department.objects.count()}')
        self.stdout.write(f'- Department Heads: {User.objects.filter(user_type=User.UserType.DEPARTMENT_HEAD).count()}')
        self.stdout.write(f'- Professors: {Professor.objects.count()}') 