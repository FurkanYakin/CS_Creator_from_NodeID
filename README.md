# CS_Creator_from_NodeID

Bu repodaki kodlar Ansys Mechanical'da hata mesajında geçen ama arayüzde görünmeyen bir node'un modelde **nerede** olduğunu bulmak için kullanılabilir.

Script, node koordinatlarını APDL `*GET` komutlarıyla okur ve her node'un konumuna Mechanical içinde bir **Coordinate System** yerleştirir. Böylece sorunlu node'un modelde nerede olduğunu ve hangi parçaya veya bağlantıya ait olduğunu hemen görebilirsiniz.



---

## Problem

Remote Point, Joint, Remote Force/Displacement gibi bağlantılar aslında uzaktaki bir noktaya kurulan **MPC bağlantılarıdır**. Bu uzak nokta, ilgili unsurun referans koordinat sisteminde oluşturulan bir **pilot node**'dur. Mechanical bu node'u arka planda oluşturur ama arayüzde göstermez.

Bu yüzden şöyle bir durumla karşılaşabilirsiniz:

> An internal solution magnitude limit was exceeded. (NodeNumber 125, Body Unknown, DOF UX)...

Mesh düğüm sayısı 100 olan bir modelde bu numaraya sahip bir node mesh'te görünmediği için hatanın kaynağını arayüzden bulmak çok zordur. Genelde tek yol APDL'e başvurmaktır.

## Çözüm

1. **Node koordinatlarını bulun.** APDL ile node'un X, Y, Z koordinatlarını okuyun:

   ```apdl
   SET,LAST
   nid = 125            ! hata mesajindaki node numarasi
   CSYS,0
   *GET,my_XN,NODE,nid,LOC,X
   *GET,my_YN,NODE,nid,LOC,Y
   *GET,my_ZN,NODE,nid,LOC,Z
   *VWRITE,nid,my_XN,my_YN,my_ZN
   ('NodeID: ',F12.0,' X: ',F12.5,' Y: ',F12.5,' Z: ',F12.5)
   ```

2. **O noktaya bir koordinat sistemi koyun.** Okunan koordinatlarda lokal bir Coordinate System oluşturun. Böylece node'un hangi parçaya veya bağlantıya ait olduğu görsel olarak ortaya çıkar.

Bu repodaki scriptler iki adımı da otomatik yapar.

---

## Dosyalar

| Dosya | Açıklama |
|---|---|
| [`NodeID_to_CS_manual.py`](NodeID_to_CS_manual.py) | Arayüz yok, tek node için çalışır. Node ID script içinde elle girilir. |
| [`NodeID_to_CS_AUTO.py`](NodeID_to_CS_AUTO.py) | Sade bir arayüz sunar. Birden fazla node ve aralık girilebilir. **Önerilen sürüm budur.** |

### `NodeID_to_CS_manual.py`

- Scriptin başındaki `node_id` ve `apdl_length_unit` değerlerini düzenleyip çalıştırırsınız.
- Solution altında `__GET_NODE_COORDINATES__` adlı bir Command Snippet oluşturur.
- Result dosyası varsa yalnızca post komutlarını çalıştırır (`ExecutePostCommands`). Yoksa `Model.Solve()` çağırır.
- Oluşturduğu koordinat sisteminin adı `CS_at_node_<ID>` olur ve eksenleri globalle hizalanır.

### `NodeID_to_CS_AUTO.py` (önerilen)

- Açılan pencereye node ID'leri girersiniz: `125`, `125,130,145`, `125-130` veya `125,130-135,150`.
- Uzunluk birimi scriptin başındaki `APDL_LENGTH_UNIT` ayarından okunur. Varsayılan değer `"mm"`'dir.
- Her node için `CS_at_node_<ID>` adında bir koordinat sistemi oluşturur. Aynı adda bir koordinat sistemi zaten varsa onu günceller.
- Koordinatları okunamayan node'ları sonuç mesajında **Failed Nodes** başlığı altında listeler.


## Kullanım

1. Analizi **Solve** edin. AUTO script bir result dosyasına ihtiyaç duyar.
2. Mechanical'da **Automation → Scripting** sekmesinden Mechanical Scripting panelini açın.
3. Script dosyasını açıp **Run** ile çalıştırın.
4. Açılan pencereye hata mesajındaki node numarasını (veya numaralarını) girip **Create Coordinate System** butonuna tıklayın.
5. Model ağacında **Coordinate Systems** altında oluşan koordinat sistemini seçin. Grafik ekranda sorunlu node'un konumu görünecektir.

Okunan koordinatlar ayrıca Mechanical log'una da yazılır:

```
NodeID: 125    X: ...    Y: ...    Z: ... [mm]
```

> 💡 Sık kullanacaksanız scripti Mechanical'da **Button Editor** ile bir toolbar butonuna atayabilirsiniz.
 
 
 
<img width="1919" height="1020" alt="Ekran Görseli" src="https://github.com/user-attachments/assets/0d6ed409-6b00-47ac-98fc-c59ebdac0ecb" />
 

---

## Notlar ve kısıtlar

- **Birim:** APDL `*GET` komutu koordinatları **çözücünün birim sisteminde** döndürür. Script içindeki birim ayarı bu sistemle aynı olmalıdır (N-mm için `mm`, MKS için `m`). Aksi halde koordinat sistemi yanlış yere konur.
- **Result dosyası:** Koordinatlar `/POST1` içinde okunduğu için analiz en az bir kez çözülmüş olmalıdır. AUTO script result dosyası bulamazsa uyarı verip durur.
- **Analiz:** Scriptler `DataModel.AnalysisList[0]` ile ağaçtaki **ilk** analizi kullanır. Projede birden fazla analiz varsa bunu kendi durumunuza göre düzenleyin.
- **Command Snippet:** Scriptler Solution altında bir Command Snippet oluşturur. Koordinat değerleri **Details** kısmında listelenir.

<img width="333" height="437" alt="image" src="https://github.com/user-attachments/assets/6a004684-5d10-430e-ad10-6c595f269996" />


---

## Destek

Desteğe ihtiyacınız olması halinde support@numesys.com.tr adresinden teknik destek talebi oluşturabilirsiniz.
