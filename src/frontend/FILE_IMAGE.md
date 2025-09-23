* Partie HTML :
```
<input id="img" type="file" accept="image/png,image/jpeg" />
```



* Partie javascript :

```
const input = document.querySelector('#img');
const f = input.files?.[0];
if (!f) throw new Error("Aucune image sélectionnée");

const form = new FormData();
form.append('designation', designation);
form.append('description', description ?? '');     // optionnel
form.append('category_code', int);
form.append('category_label', string);
form.append('file', f, f.name);

await fetch('https://api-gateway:9000/api/protected/create_ad', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body: form,                                    
});
```

