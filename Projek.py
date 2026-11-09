from abc import ABC, abstractmethod
from datetime import date, timedelta

class InsufficientFundsException(Exception):
  pass

class LimitPinjamanException(Exception):
  pass

class UsernameSudahDipakaiException(Exception):
  pass

class LoginGagalException(Exception):
  pass

class SyaratSaldo:
  @staticmethod
  def cekJumlah(jumlah):
    if not isinstance(jumlah,(int,float)):
      raise ValueError("Invalid, Jumlah harus berupa angka")
    if jumlah<= 0:
      raise ValueError("Jumlah harus lebih dari 0")
  @staticmethod
  def cekCukup(saldo,jumlah):
    if jumlah > saldo:
      raise InsufficientFundsException("Saldo tidak cukup")
    
class User(ABC):
  @property
  def saldo(self):
   return self._saldo
  @abstractmethod
  def getRole(self):
    pass

  def __init__(self, username,password,nama,alamat,email,):
    self.username = username
    self._password = password
    self.nama = nama
    self.alamat = alamat
    self.email = email
    self._saldo = 0



  def tampilProfile(self):
    peran = self.getRole()
    print(f"Peran            : {peran}")
    print(f"Username         : {self.username}")
    print(f"Nama             : {self.nama}")
    print(f"Alamat           : {self.alamat}")
    print(f"Email            : {self.email}")
    print(f"Saldo            : {self._saldo}")

  def deposit(self,jumlah):
    SyaratSaldo.cekJumlah(jumlah)
    self._saldo += jumlah

  def withdraw(self, jumlah):
    SyaratSaldo.cekJumlah(jumlah)
    SyaratSaldo.cekCukup(self._saldo, jumlah)
    self._saldo -= jumlah

  def cekPass(self,password):
    return self._password == password

class Platform:
  def __init__(self):
    self._users = {}

  def daftar(self,user):
    if user.username in self._users:
      raise UsernameSudahDipakaiException("Username sudah dipakai")
    self._users[user.username] = user

  def login(self,username,password):
    user =self._users.get(username)
    if user is None or not user.cekPass(password):
      raise LoginGagalException("Username atau Password salah")
    return user

  def daftarLender(self):
    hasil = []
    for u in self._users.values():
      if u.getRole() == "Lender":
        hasil.append(u)
    return hasil

class Loan:
  bungaTahunan = 0.12
  def __init__(self,borrower,lender,jumlah,tenor,tujuan):
    if jumlah <= 0:
      raise ValueError("Jumlah pinjaman harus lebih dari 0")
    if tenor <= 0:
      raise ValueError("Tenor harus lebih dari 0")
    self.borrower = borrower
    self.lender = lender
    self.jumlah = jumlah
    self.tenor = tenor
    self.tujuan=tujuan
    self.status = "[Pending]"
    self.jadwal = []


  def hitungCicilan(self):
    r = self.bungaTahunan / 12
    return self.jumlah*r/(1-(1+r)**-self.tenor)

  def buatJadwal(self ,tanggalMulai):
    r = self.bungaTahunan/12
    cicilanTetap = self.hitungCicilan()
    sisa = self.jumlah
    self.jadwal =[]

    for n in range(1,self.tenor+1):
      bunga = round(sisa*r,2)
      if n == self.tenor:
        pokok = sisa
      else:
        pokok = round(cicilanTetap - bunga,2)
      sisa = round(sisa-pokok,2)
      jatuhTempo = tanggalMulai + timedelta(days=30*n)
      self.jadwal.append(Cicilan(n,jatuhTempo,pokok,bunga))

  def cicilanBerikutnya(self):
    for c in self.jadwal:
      if not c.tanggalBayar:
        return c
    return None

  def __iter__(self):
    return IteratorCicilan(self.jadwal)

  def cicilanBelumLunas(self):
    for c in self.jadwal:
      if not c.lunas:
        yield c
  
  def sisaPinjaman(self):
    return sum(c.pokok for c in self.cicilanBelumLunas())

  def tampilJadwal(self):
    print(f"Pinjaman  : {self.tujuan}")
    print(f"Peminjam  : {self.borrower.nama}")
    print(f"Pemberi   : {self.lender.nama}")
    print(f"Status    : {self.status}")
    print(f"Sisa pokok: {self.sisaPinjaman():,.0f}")
    nxt = self.cicilanBerikutnya()
    if nxt:
      print(f"Cicilan berikutnya : {nxt.jatuhTempo} = {nxt.total:,.0f}")
    print("="*60)
    print(f"{'No':<4}{'Jatuh Tempo':<14}{'Pokok':>12}{'Bunga':>12}{'Total':>12}  Status")
    for c in self:
      status = "LUNAS" if c.lunas else "BELUM"
      print(f"{c.nomor:<4}{str(c.jatuhTempo):<14}{c.pokok:>12,.0f}{c.bunga:>12,.0f}{c.total:>12,.0f}  {status}")

class Borrower(User):

  @property
  def skor(self):
    return self._skor

  @property
  def batasPinjaman(self):
    if self._skor == 100:
      return 10000000
    elif self._skor >= 40:
      return 5000000
    else:
      return 1000000

  def __init__(self, username, password, nama, alamat, email):
    super().__init__(username, password, nama, alamat, email)
    self.daftarPinjaman = []
    self._skor = 80
    self.beruntun = 0

  def tampilProfile(self):
    super().tampilProfile()
    print(f"Credit Score     : {self._skor}")
    print(f"Limit Pinjaman   : {self.batasPinjaman}")

  def getRole(self):
    return "Borrower"

  def pengajuanPinjaman(self, lender,jumlah, tenor, tujuan):
    loan = Loan(self, lender,jumlah,tenor, tujuan)
    if self.totalPinjaman() + jumlah > self.batasPinjaman:
      raise LimitPinjamanException("Melebihi limit pinjaman")
    self.daftarPinjaman.append(loan)
    lender.daftarPengajuan.append(loan)
    return loan

  def totalPinjaman(self):
    total = 0
    for loan in self.daftarPinjaman:
      if loan.status in ("[Pending]", "[Disetujui]"):
        total += loan.jumlah
    return total
  def catatPembayaran(self, tepatWaktu):
    if tepatWaktu:
      self.beruntun +=1
      if self.beruntun == 3:
        self._skor += 5
        self.beruntun = 0
    else:
      self._skor -=10
      self.beruntun = 0
    self._skor = min(100,self._skor)
    self._skor = max(0,self._skor)

  def bayarCicilan(self, loan, hariIni = None):
    if hariIni is None:
      hariIni = date.today()
    if loan.borrower is not self:
      raise ValueError("Pinjaman ini bukan milik anda")
    if loan.status != "[Disetujui]":
      raise ValueError("Pinjaman tidak dalam masa cicilan")
    cicilan = loan.cicilanBerikutnya()
    self.withdraw(cicilan.total)
    loan.lender.deposit(cicilan.total)
    cicilan.lunas = True
    cicilan.tanggalBayar = hariIni
    self.catatPembayaran(hariIni <= cicilan.jatuhTempo)
    if loan.cicilanBerikutnya()is None:
      loan.status = "[Lunas]"
    return cicilan

class Lender(User): 
  def getRole(self):
    return "Lender"
  def __init__(self, username, password, nama, alamat, email):
    super().__init__(username, password, nama, alamat, email)
    self.daftarPengajuan = []

  def setujuPinjaman(self, loan):
    if loan.lender is not self:
      raise ValueError("Pengajuan ini bukan untuk anda")
    if loan.status !="[Pending]":
      raise ValueError("Status pinjaman sudah diputuskan")
    self.withdraw(loan.jumlah)
    loan.borrower.deposit(loan.jumlah)
    loan.status = "[Disetujui]"
    loan.buatJadwal(date.today())

  def tolakPinjaman(self, loan):
    if loan.lender is not self:
      raise ValueError("Pengajuan ini bukan untuk anda")
    if loan.status !="[Pending]":
      raise ValueError("Status pinjaman sudah diputuskan")
    loan.status = "[Ditolak]"

  def daftarPending(self):
    queue = []
    for pending in self.daftarPengajuan:
      if pending.status == "[Pending]":
        queue.append(pending)
    return queue

class Cicilan:
  def __init__(self, nomor, jatuhTempo, pokok, bunga):
    self.nomor = nomor
    self.jatuhTempo = jatuhTempo
    self.pokok = pokok
    self.bunga = bunga
    self.total = round(self.pokok + bunga,2)
    self.lunas = False
    self.tanggalBayar = None

class IteratorCicilan:
  def __init__(self, jadwal):
    self._jadwal = jadwal
    self._index = 0

  def __iter__(self):
    return self

  def __next__(self):
    if self._index >= len(self._jadwal):
      raise StopIteration
    cicilan = self._jadwal[self._index]
    self._index += 1
    return cicilan

def inputAngka(pesan):
  while True:
    try:
      return float(input(pesan))
    except ValueError:
      print("Input hanya terdiri dari angka 0-9")

def daftarBaru(sistem):
  peran = input("Peran (1. Borrower  2. Lender): ")
  username = input("Username: ")
  password = input("Password: ")
  nama = input("Nama: ")
  alamat = input("Alamat: ")
  email = input("Email: ")
  if peran == "1":
    user = Borrower(username, password, nama, alamat, email)
  elif peran == "2":
    user = Lender(username, password, nama, alamat, email)
  else:
    print("Pilihan tidak dikenal")
    return
  try:
    sistem.daftar(user)
    print("Pendaftaran berhasil")
  except UsernameSudahDipakaiException as e:
    print("Gagal:", e)

def menuAwal(sistem):
  while True:
    print("\n1. Daftar\n2. Login\n3. Keluar")
    pilih = input("> ")
    if pilih == "1":
      daftarBaru(sistem)
    elif pilih == "2":
      username = input("Username :")
      password = input("Password : ")
      try:
        user = sistem.login(username, password)
        print(f"Selamat datang, {user.nama} ({user.getRole()})")
        if user.getRole() == "Borrower":
          menuBorrower(user,sistem)
        else:
          menuLender(user)
      except LoginGagalException as e:
        print("Gagal:", e)
    elif pilih == "3":
      print("Sampai jumpa")
      break

def menuBorrower(user,sistem):
  while True:
    print(f"\n---- Menu Borrower : {user.nama} ----")
    print("1. Profil\n2. Deposit\n3. Withdraw\n4. Ajukan Pinjaman\n5. Lihat Pinjaman\n6. Bayar Cicilan\n7. Logout")
    pilih = input(">")

    try:
      if pilih == "1":
        user.tampilProfile()
      elif pilih == "2":
        user.deposit(inputAngka("Jumlah deposit : "))
        print("Tambah Saldo Berhasil")
        print(f"Saldo Sekarang : {user.saldo:,.2f}")
      elif pilih =="3":
        user.withdraw(inputAngka("Jumlah withdraw : "))
        print("Tarikan Saldo Berhasil")
        print(f"Saldo Sekarang : {user.saldo:,.2f}")
      elif pilih == "4":
        daftar = sistem.daftarLender()
        if not daftar:
          print("Belum ada Lender terdaftar")
        else:
          for i, l in enumerate(daftar, 1):
            print(f"{i}. {l.nama}")
          nomor = int(inputAngka("Pilih Lender (nomor): "))
          if not 1 <= nomor <= len(daftar):
            print("Nomor tidak valid")
          else:
            lender = daftar[nomor - 1]
            jumlah = inputAngka("Jumlah pinjaman: ")
            tenor = int(inputAngka("Tenor (bulan): "))
            tujuan = input("Tujuan: ")
            user.pengajuanPinjaman(lender, jumlah, tenor, tujuan)
            print("Pengajuan terkirim, menunggu keputusan Lender")
      elif pilih == "5":
        if not user.daftarPinjaman:
          print("Belum ada pinjaman")
        for loan in user.daftarPinjaman:
          loan.tampilJadwal()
          print()
      elif pilih == "6":
        aktif = []
        for loan in user.daftarPinjaman:
          if loan.status == "[Disetujui]":
            aktif.append(loan)

        if not aktif:
          print("Tidak ada cicilan yang perlu dibayar")
        else:
          for i, loan in enumerate(aktif,1):
            nxt = loan.cicilanBerikutnya()
            print(f"{i}.{loan.tujuan} | cicilan ke {nxt.nomor} | {nxt.total:,.2f}")
          nomor = int(inputAngka("Pilih pinjaman (nomor) : "))
          if 1 <= nomor <= len(aktif):
            loan = aktif[nomor - 1]
            cicilan = user.bayarCicilan(loan)
            print(f"Cicilan ke-{cicilan.nomor} sebesar {cicilan.total:,.0f} berhasil dibayar")
          else:
            print("Nomor tidak valid")

      elif pilih == "7":
        print("Anda sudah logout")
        break
      else:
        print("Pilihan tidak dikenal")
    except (InsufficientFundsException, LimitPinjamanException, ValueError) as e:
      print("Gagal:", e)

def menuLender(user):
  while True:
    print(f"\n---- Menu Lender : {user.nama} ----")
    print("1. Profil \n2. Deposit \n3. Withdraw \n4. Lihat Pengajuan \n5. Setujui/Tolak \n6. Lihat Pinjaman yang Didanai \n7. Logout ")
    pilih = input(">")

    try:
      if pilih == "1":
        user.tampilProfile()
      elif pilih == "2":
        user.deposit(inputAngka("Jumlah deposit : "))
        print("Tambah Saldo Berhasil")
        print(f"Saldo Sekarang : {user.saldo:,.2f}")
      elif pilih =="3":
        user.withdraw(inputAngka("Jumlah withdraw : "))
        print("Tarikan Saldo Berhasil")
        print(f"Saldo Sekarang : {user.saldo:,.2f}")
      elif pilih == "4":
        pending = user.daftarPending()
        if not pending:
          print("Tidak ada pengajuan masuk")
        else:
          for i, loan in enumerate(pending,1):
            print(f"{i}.{loan.borrower.nama} | {loan.jumlah:,.2f} | Tenor {loan.tenor} | {loan.tujuan}")

      elif pilih == "5":
        pending = user.daftarPending()
        if not pending:
          print("Tidak ada pengajuan")
        else:
          for i, loan in enumerate(pending,1):
             print(f"{i}.{loan.borrower.nama} | {loan.jumlah:,.2f} | Tenor {loan.tenor} | {loan.tujuan}")
          nomor = int(inputAngka("Pilih Nomor : "))
          if not 1 <= nomor <= len(pending):
            print("Nomor tidak valid")
          else:
            loan = pending[nomor -1]
            keputusan = input("Setujui (s) / Tolak (t) : ")
            if keputusan.lower() == "s":
              user.setujuPinjaman(loan)
              print("PInjaman disetujui")
            elif keputusan.lower() == "t":
              user.tolakPinjaman(loan)
              print("Pinjaman ditolak")
            else:
              print("Pilihan tidak ada")
      elif pilih == "6":
        didanai = []
        for loan in user.daftarPengajuan:
          if loan.status in ("[Disetujui]", "[Lunas]"):
            didanai.append(loan)
        if not didanai:
          print("Belum ada riwayat peminjaman")
        for loan in didanai:
          loan.tampilJadwal()
          print()

      elif pilih == "7":
        print("Anda sudah logout")
        break
      else:
        print("Pilihan Tidak Ada")
    except (InsufficientFundsException,ValueError) as e:
      print("Gagal : ",e)
    
      
      

sistem = Platform()
menuAwal(sistem)