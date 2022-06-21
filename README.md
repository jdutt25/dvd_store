# dvd_store
REST API

Please refer to API Spec for detailed information on how to use this REST API: https://github.com/jdutt25/dvd_store/blob/master/API_Spec.pdf

Users must have valid JWT (may obtained with Google OAuth 2.0 at application URL) to utilize application. 
All CRUD operations may be performed for non-user entities (Customers and DVDs), but DVDs are a protected entity that may only be accessed by verified Store Managers 
(authenticated by JWT sub). 
