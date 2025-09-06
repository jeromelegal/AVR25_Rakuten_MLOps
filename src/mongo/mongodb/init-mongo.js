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
        required: ["designation", "description", "image_name", "bucket_name", "created_at", "created_by"],
        properties: {
          designation: { bsonType: "string" },
          description: { bsonType: "string" },
          image_name:  { bsonType: "string" },
          bucket_name: { bsonType: "string" },
          created_at:  { bsonType: "string" },
          created_by:  { bsonType: "string" }
        }
      }
    }
});

// Create categories collection
db.getSiblingDB('file_storage').createCollection("categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["code", "label"],
      properties: {
        code:      { bsonType: "int" },
        label:     { bsonType: "string" }
      }
    }
  }
});
db.categories.createIndex({ code: 1 }, { unique: true });

// Create ad_categories collection
db.getSiblingDB('file_storage').createCollection("ad_categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["ad_id", "category_id"],
      properties: {
        ad_id:       { bsonType: "objectId" },
        category_id: { bsonType: "objectId" }
      }
    }
  }
});
db.ad_categories.createIndex({ ad_id: 1 }, { unique: true });
db.ad_categories.createIndex({ category_id: 1 });
