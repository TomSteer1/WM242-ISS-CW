actor Client

participant Client
participant MediCloud
participant KMS
participant Auth

title MediCloud
Client -> MediCloud: Requests /
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud --> Client: Redirect to /files
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: Home Page
end

Client-> MediCloud: Requests /files
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud -> MediCloud: Loads files from database \nSends the user files they have access to
MediCloud --> Client: Files
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: Login Page
end

Client-> MediCloud: Makes Post Request to /uplaodFile
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud -> MediCloud: Checks the file is valid
alt Valid request
MediCloud -> KMS: Generates a key for the file
KMS --> MediCloud: Key, IV
MediCloud -> MediCloud: Encrypts and saves the file using AES CFB \nAdds the file to the database
MediCloud --> Client: Redirect to /files
else Invalid request
MediCloud --> Client: Invalid file message, redirect to /files
end
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: Login Page
end

Client-> MediCloud: Makes Request to /file/<id>
MediCloud -> MediCloud: Check file exists
alt File exists
MediCloud -> MediCloud: Check if file is public
alt Public file
MediCloud -> KMS: File ID
KMS --> MediCloud: Key, IV
MediCloud -> MediCloud: Decrypts the file
MediCloud --> Client: File
else Private file
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud -> MediCloud: Checks the permissions of the file for the user
alt Authorised
MediCloud -> KMS: File ID
KMS --> MediCloud: Key, IV
MediCloud -> MediCloud: Decrypts the file
MediCloud --> Client: File
else Unauthorised
MediCloud --> Client: 404
end
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: 404
end
end
else File does not exist
MediCloud --> Client: 404
end

Client -> MediCloud: Makes POST Request to /togglePublic or /toggleShared
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud -> MediCloud: Checks if file exists
alt File exists
MediCloud -> MediCloud: Checks if the user owns the file
alt Has permission
MediCloud -> MediCloud: Gets the current status of the public/shared parameter \nFlips the boolean \nUpdates the file in DB
MediCloud --> Client: Redirect to /files
else Does not have permission
MediCloud --> Client: 403
end
else File not found
MediCloud --> Client: 404
end
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: Login Page
end

Client -> MediCloud: Makes POST Request to /deleteFile
MediCloud-> Auth: Check Authentication and Roles (Staff)
alt Authenticated
Auth --> MediCloud: User
MediCloud -> MediCloud: Checks if file exists
alt File exists
MediCloud -> MediCloud: Checks if the user owns the file
alt Has permission
MediCloud -> MediCloud: Removes file from share and DB
MediCloud -> KMS: Delete file keys
KMS --> MediCloud: 200
MediCloud --> Client: Redirect to /files
else Does not have permission
MediCloud --> Client: 403
end
else File not found
MediCloud --> Client: 404
end
else Unauthenticated
Auth --> MediCloud: Unauthorised
MediCloud --> Client: Login Page
end
