# ISS

## SSO
    - Uses secrets instead of os.randombytes as secrets is more secure
    - ppbkdf2_sha256
## RBAC
    - Auth server stores permission bits
    - Auth module has checkPermission function which caches for 2 minutes and checks the users permissions
    - Has the roles
        0 - Banned
        1 - User
        2 - Staff
        4 - Medical Staff
        8 - Finance
        16 - HR
        32 - Admin
## Encryption at Rest (Justification needed)
### DB
    - Database is encrypted using SQLCipher
    - Files 
## Systems
- MedRecords
- FinCare
- CareConnect
- Prescriptions
- MediCloud


