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
        ad_id: { bsonType: "int"}, 
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
        created_at: { bsonType: "date" }
      }
    }
  }
});

// Create searching index
db.ads.createIndex(
  { designation: "text", description: "text" },
  {
    default_language: "french",
    weights: { designation: 8, description: 5 },
    name: "ads_search"
  }
);
// Create filters index
// Index for text search
db.ads.createIndex(
  { designation: "text", description: "text" },
  { default_language: "french", weights: { designation: 8, description: 5 }, name: "ads_search" }
);
// Index for unicity on ad_id
db.ads.createIndex({ ad_id: 1 }, { unique: true, name: "ad_id_unique" });
// Index for category listing sorted by date
db.ads.createIndex({ category: 1, created_at: -1 }, { name: "cat_created" });
// Index global sorting by date
db.ads.createIndex({ created_at: -1 }, { name: "created_desc" });