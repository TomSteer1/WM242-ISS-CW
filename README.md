# ISS

## Instructions
### Credentials
The app will initially create 4 users (one for each role)
```
user:user
doctor:doctor
finance:Finance
hr:hr
admin:admin
superadmin:superadmin
```


### Initial
- Run the following commands first
```bash
# Adds the dns records to the host file
echo "127.0.0.1   auth.meditech.com care.meditech.com fincare.meditech.com cloud.meditech.com records.meditech.com prescriptions.meditech.com portal.meditech.com" | sudo tee -a /etc/hosts
```
#### Docker Method (simpler)
- Make sure to have docker and docker-compose installed
- Then run `./start.sh` (as sudo if not using rootless docker)
#### Local Method
- Make sure to have docker and tmux installed
- Run the following in the root folder before the first launch
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r Services/Global/requirements.txt
```
- Then run `./tmux-start.sh`

#### Troubleshooting
- Can't connect to the server
    1. Ensure there are host records in the /etc/hosts file
    2. Ensure the app is running (Try doing `curl localhost -v`. It should preform a redirect)
- Can't connect to docker socket
    1. Run the script as sudo

## App Requirements

### SSO/Invidivual Auth
    - Uses secrets instead of os.randombytes as secrets is more secure
    - ppbkdf2_sha256
### RBAC
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
### Encryption at Rest (Justification needed)
#### DB
    - Database is encrypted using SQLCipher
    - Files are encrypted using AES Stream based ciphers
        - Each file has it's own key stored by the kms
### Systems
- MedRecords
    - Only accessible to doctors
    - Doctors can add medical records to patients
- FinCare
    - Only accessible to finance team
    - Team can add purchases
    - Only admins can remove
- CareConnect
    - Users can log in to view their own records
    - Medical Staff can login to view all records
- Prescriptions
    - Patients can view their prescriptions
    - Doctors can add/delete prescriptions
    - Admins can add/delete medicines
- MediCloud
    - Users with the role "Staff" can access the file portal
    - Staff can upload files to the server and then set the file to be accessible to all staff or everyone (for sharing of leaflets for example)
- Auth
    - HR can modify user permissions
    - Admins can modify application tok


