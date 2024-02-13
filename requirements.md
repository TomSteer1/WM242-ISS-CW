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
    - Files are encrypted using AES Stream based ciphers
        - Each file has it's own key stored by the kms
## Systems
- MedRecords
- FinCare
- CareConnect
    - Users can log in to view their own records
    - Medical Staff can login to view all records
- Prescriptions
- MediCloud
    - Users with the role "Staff" can access the file portal
    - Staff can upload files to the server and then set the file to be accessible to all staff or everyone (for sharing of leaflets for example)


