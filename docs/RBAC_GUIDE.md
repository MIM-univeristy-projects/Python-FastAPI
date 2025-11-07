# Role-Based Access Control (RBAC) Implementation

## Overview

This FastAPI application now includes role-based access control with two user roles:

- **USER**: Default role for regular users
- **ADMIN**: Administrative role with access to protected endpoints

## User Roles

### UserRole Enum

```python
class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
```

## Authentication Flow

### 1. Register a User

**Endpoint**: `POST /users/register`

New users are created with:

- Default role: `USER`
- Active status: `true`

```json
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "Password1!"
}
```

### 2. Login

**Endpoint**: `POST /users/token`

Returns JWT token **and** user information including role:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser",
    "role": "user",
    "is_active": true,
    "created_at": "2025-11-07T17:00:00Z"
  }
}
```

**Frontend Integration**: The response includes the user's role, allowing Angular to:

- Store the role in local storage/session
- Implement role-based routing guards
- Show/hide components based on user role

### 3. Get Current User

**Endpoint**: `GET /users/me`
**Auth Required**: Yes (any authenticated user)
**Returns**: Current user information with role

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "role": "user",
  "is_active": true,
  "created_at": "2025-11-07T17:00:00Z"
}
```

## Admin-Only Endpoints

### Get User by Username

**Endpoint**: `GET /users/admin/username/{user_username}`
**Auth Required**: Yes (admin role only)
**Returns**: User information

### Get User by Email

**Endpoint**: `GET /users/admin/email/{user_email}`
**Auth Required**: Yes (admin role only)
**Returns**: User information

## Creating an Admin User

Run the provided script to create an admin user:

```bash
python create_admin.py
```

Default admin credentials:

- Username: `admin`
- Email: `admin@example.com`
- Password: `Admin123!`
- Role: `admin`

**Important**: Change the password in production!

## Frontend Integration (Angular)

### 1. Store User Role on Login

```typescript
login(username: string, password: string) {
  return this.http.post<TokenResponse>('/users/token', { username, password })
    .pipe(
      tap(response => {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user_role', response.user.role);
        localStorage.setItem('user_info', JSON.stringify(response.user));
      })
    );
}
```

### 2. Role-Based Route Guards

```typescript
@Injectable()
export class AdminGuard implements CanActivate {
  canActivate(): boolean {
    const role = localStorage.getItem('user_role');
    return role === 'admin';
  }
}
```

### 3. Conditional Component Rendering

```typescript
// In component
isAdmin(): boolean {
  return localStorage.getItem('user_role') === 'admin';
}
```

```html
<!-- In template -->
<div *ngIf="isAdmin()">
  <admin-panel></admin-panel>
</div>
```

## Security Considerations

1. **Token Validation**: All protected endpoints validate JWT tokens
2. **Role Checking**: Admin endpoints verify user role before granting access
3. **Password Security**: Passwords are hashed using Argon2
4. **Active Status**: Inactive users cannot access protected endpoints

## Error Responses

### 401 Unauthorized

- Invalid or missing token
- Invalid credentials

### 403 Forbidden

- User lacks required role (e.g., trying to access admin endpoint as regular user)

```json
{
  "detail": "You do not have permission to access this resource"
}
```

### 404 Not Found

- User not found in admin lookup endpoints

## Migration Note

If you have existing users in the database, they won't have the `role` field. You need to:

1. Drop and recreate the database, OR
2. Run a migration to add the role column with default value 'user'

The `create_admin.py` script handles role assignment for the admin user.
