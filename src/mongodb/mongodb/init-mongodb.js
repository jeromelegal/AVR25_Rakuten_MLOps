const crypto = require('crypto');

use admin;
db.createUser({
  user: 'root',
  pwd: 'example',
  roles: [{ role: 'root', db: 'admin' }]
});

db.createCollection('users');

db.getSiblingDB('db_rakuten').createRole({
  role: 'dbManager',
  privileges: [
    { resource: { db: 'db_rakuten', collection: '' }, actions: ['find', 'insert', 'update', 'remove'] }
  ],
  roles: []
});

db.getSiblingDB('db_rakuten').createUser({
  user: 'db_manager_user',
  pwd: 'db_manager_user_password',
  roles: [{ role: 'dbManager', db: 'db_rakuten' }]
});


db.getSiblingDB('db_rakuten').createRole({
  role: 'userManager',
  privileges: [
    { resource: { db: 'db_rakuten', collection: 'users' }, actions: ['find', 'insert', 'update', 'remove'] }
  ],
  roles: []
});

db.getSiblingDB('db_rakuten').createUser({
  user: 'user_manager',
  pwd: 'usermanagerpassword',
  roles: [{ role: 'userManager', db: 'db_rakuten' }]
});

// Create ads collection
db.getSiblingDB('db_rakuten').createCollection("ads", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id","user", "designation", "categories", "images", "created_at"],
      properties: {
        _id: { bsonType: "int" },
        user: {
          bsonType: "object",
          required: ["id","username"],
          properties: {
            id: { bsonType: "int" },
            username: { bsonType: "string" }
          }
        },
        designation: { bsonType: "string" },
        description: { bsonType: "string" },
        categories: { bsonType: "string" },
        images:     { bsonType: "array", items: { bsonType: "string" } },
        created_at: { bsonType: "date" }
      }
    }
  }
});

// Create index
db.getSiblingDB('db_rakuten').ads.createIndex(
  {
    designation: 'text',
    description: 'text',
    categories:  'text',
    images:      'text',
    'user.username': 'text'
  },
  {
    weights: {
      designation: 10,
      description: 10,
      categories: 5,
      images: 1,
      'user.username': 1,
    },
    name: 'ads_search'
  }
);