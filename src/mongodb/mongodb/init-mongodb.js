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

// Create ads collection
db.getSiblingDB('file_storage').createCollection("ads", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user", "designation", "category", "created_at"],
      properties: {
        _id: { bsonType: "objectId" },
        user: {
          bsonType: "object",
          required: ["id","username"],
          properties: {
            id: { bsonType: "int" },
            username: { bsonType: "string" }
          }
        },
        designation: { bsonType: "string" },
        description: { bsonType: ["string", "null"] },
        category: { bsonType: "string" },
        images: {
          bsonType: ["array", "null"],
          items: {
            bsonType: "object",
            required: ["image_uuid", "bucket_path"],
            additionalProperties: false,
            properties: {
              image_uuid: { bsonType: "string" },
              bucket_path: { bsonType: "string" }
            }
          }
        },
        created_at: { bsonType: "string" }
      }
    }
  }
});

// Create index
db.getSiblingDB('file_storage').ads.createIndex(
  {
    designation: 'text',
    description: 'text',
    category:  'text',
    images:      'text',
    'user.username': 'text'
  },
  {
    weights: {
      designation: 10,
      description: 10,
      category: 5,
      images: 1,
      'user.username': 1,
    },
    name: 'ads_search'
  }
);
