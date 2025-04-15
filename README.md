# bragboard


## Database Structure

The following ER diagram represents the data model for the pinball leaderboard application:

```mermaid
erDiagram
    MACHINE {
        int id PK
        string name
        string model
    }

    GAME {
        int id PK
        int machine_id FK
        datetime created_at
    }

    PLAY {
        int id PK
        int game_id FK
        int user_id FK "nullable"
        string initials
        int score
        datetime played_at
    }

    USER {
        int id PK
        string username
        string full_name
        string email
    }

    TIME_SERIES_DATA {
        int id PK
        int play_id FK
        int score
        int ball_number
        int tilt_warnings
        datetime timestamp
    }

    MACHINE ||--o{ GAME : "has"
    GAME ||--o{ PLAY : "has 1-4"
    PLAY }o--o| USER : "belongs to"
    PLAY ||--o{ TIME_SERIES_DATA : "has"

```

### Entity Relationships

- **Machine**: Represents a physical pinball machine
- **Game**: A session on a specific machine
- **Play**: An individual player's turn within a game (1-4 players per game)
- **User**: A registered user who can be linked to plays
- **Time Series Data**: Detailed metrics tracking score over time, ball in play, and tilt warnings
