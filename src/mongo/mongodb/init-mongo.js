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

// create ads collection
db.getSiblingDB('file_storage').createCollection('ads', {
  validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["ad_id", "designation", "description", "image", "created_at", "created_by"],
        properties: {
          ad_id:       { bsonType: "string" },
          designation: { bsonType: "string" },
          description: { bsonType: "string" },
          image:       { bsonType: "string" },
          created_at:  { bsonType: "string" },
          created_by:  { bsonType: "string" }
        }
      }
    }
});
