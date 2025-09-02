const crypto = require('crypto');

use admin;
db.createUser({
  user: 'root',
  pwd: 'example',
  roles: [{ role: 'root', db: 'admin' }]
});

db.createCollection('users');

db.getSiblingDB('file_storage').createRole({
  role: 'dbManager',
  privileges: [
    { resource: { db: 'file_storage', collection: '' }, actions: ['find', 'insert', 'update', 'remove'] }
  ],
  roles: []
});

db.getSiblingDB('file_storage').createUser({
  user: 'db_manager_user',
  pwd: 'db_manager_user_password',
  roles: [{ role: 'dbManager', db: 'file_storage' }]
});


db.getSiblingDB('file_storage').createRole({
  role: 'userManager',
  privileges: [
    { resource: { db: 'file_storage', collection: 'users' }, actions: ['find', 'insert', 'update', 'remove'] }
  ],
  roles: []
});

db.getSiblingDB('file_storage').createUser({
  user: 'user_manager',
  pwd: 'usermanagerpassword',
  roles: [{ role: 'userManager', db: 'file_storage' }]
});



