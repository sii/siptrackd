from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Random
import random
import traceback

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import errors
from siptrackdlib import storagevalue
from siptrackdlib import log
from siptrackdlib import permission

class PasswordTree(treenodes.BaseNode):
    class_id = 'PT'
    class_name = 'password tree'

    def __init__(self, oid, branch):
        super(PasswordTree, self).__init__(oid, branch)

class PasswordCategory(treenodes.BaseNode):
    class_id = 'PC'
    class_name = 'password category'
    
    def __init__(self, oid, branch):
        super(PasswordCategory, self).__init__(oid, branch)

class Password(treenodes.BaseNode):
    """Store passwords.

    Used to store passwords, if an optional key is given (as a PasswordKey
    object) the password will be encrypted on disk and in memory and only
    accessible if the PasswordKey is unlocked.
    """
    class_id = 'P'
    class_name = 'password'

    def __init__(self, oid, branch, password = None, key = None,
            unicode = True, pk_password = None):
        """Init.

        password is the plaintext password.
        key is an optional password key.
        unicode determines whether the password should go through
            character conversion (if it's a unicode password)
        """
        super(Password, self).__init__(oid, branch)
        if type(password) in [str, unicode] and unicode:
            password = password.encode('utf-8')
        self._password = storagevalue.StorageValue(self, 'password', password)
        self._password_key = storagevalue.StorageNode(self, 'key', key)
        self._lock_data = storagevalue.StorageValue(self, 'password-lockdata')
        self.unicode = unicode
        self._pk_password = pk_password

    def _created(self, user):
        """Store the password and extra data."""
        super(Password, self)._created(user)
        if type(self._password.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid password in password object')
        if self.password_key:
            if not self.password_key.canEncryptDecrypt(self._pk_password, user):
                raise errors.SiptrackError('unable to access password key')
            self._password_key.commit()
            password, self.lock_data = self.password_key.encrypt(self._password.get(),
                    self._pk_password, user)
            self._password.set(password)
        else:
            self._password.commit()
        self._pk_password = None

    def _loaded(self, data = None):
        """Load the password from disk.

        If the password has been stored encrypted it will not be decrypted
        here.
        """
        super(Password, self)._loaded(data)
        self._password_key.preload(data)
        self._lock_data.preload(data)
        self._password.preload(data)
        self._pk_password = None

    def getPassword(self, pk_password, user):
        """Returns the password.
        
        If it has been encrypted with a PasswordKey decrypt it first.
        """
        password = self._password.get()
        if self.password_key:
            try:
                if self.password_key.canEncryptDecrypt(password = pk_password,
                        user = user):
                    password = self.password_key.decrypt(password, self.lock_data,
                            pk_password, user)
                else:
                    password = ''
            # Decryption failed.
            except errors.SiptrackError, e:
                password = ''
        if self.unicode and type(password) != unicode:
            try:
                password = password.decode('utf-8')
            except UnicodeDecodeError:
                password = ''
            except Exception, e:
                password = ''
                tbmsg = traceback.format_exc()
                log.msg(tbmsg)
        return password

    def setPassword(self, user, password):
        """Set a new password in the Password."""
        if type(password) not in [str, unicode]:
            raise errors.SiptrackError('invalid password in password object')
        if self.password_key:
            if not self.password_key.canEncryptDecrypt(None, user):
                raise errors.SiptrackError('unable to access password key')
            password, self.lock_data = self.password_key.encrypt(password, None, user)
            self._password.set(password)
        else:
            self._password.set(password)

    def setPasswordKey(self, user, password_key):
        """Set a new password key in the Password."""
        if self.password_key and not self.password_key.canEncryptDecrypt(None, user):
            raise errors.SiptrackError('unable to access existing password key')
        if password_key and not password_key.canEncryptDecrypt(None, user):
            raise errors.SiptrackError('unable to access new password key')
        password = self.getPassword('', user)
        self._password_key.set(password_key)
        self.setPassword(user, password)

    def _get_lock_data(self):
        return self._lock_data.get()
    def _set_lock_data(self, val):
        self._lock_data.set(val)
    lock_data = property(_get_lock_data, _set_lock_data)

    def _get_password_key(self):
        return self._password_key.get()
    def _set_password_key(self, val):
        self._password_key.set(val)
    password_key = property(_get_password_key, _set_password_key)

class PasswordKey(treenodes.BaseNode):
    """A password key used to encrypt/decrypt password.
    
    A PasswordKey is used encrypt/decrypt passwords for Password
    objects with a key that is stored in the PasswordKey object.
    On creation, a random string (32 bytes) is generated. This string is
    used to encrypt passwords with the encrypt/decrypt methods. The
    password string is stored encrypted so that the PasswordKeys key is
    needed to access it. Verification that the correct key has been supplied
    is also performed so that an invalid password is not used to encrypt
    passwords with .encrypt.
    """
    class_id = 'PK'
    class_name = 'password key'

    def __init__(self, oid, branch, key = None):
        """Init.

        self.password : The PasswordKeys real key (password)
        self._encyption_string : The encrypted form of the password used with
            encrypt/decrypt methods.
        self._verify_clear : Clear text version of the verifier string.
        self._verify_crypt : Encrypted version of the verifier string.
            Encrypted with self.key, not self.password.
        """
        super(PasswordKey, self).__init__(oid, branch)
        self.password = key
        self._encryption_string = None
        self._verify_clear = None
        self._verify_crypt = None
        self._encryption_string = storagevalue.StorageValue(self, 'password', None)
        self._verify_clear = storagevalue.StorageValue(self, 'verify-clear', None)
        self._verify_crypt = storagevalue.StorageValue(self, 'verify-crypt', None)
        self._subkey_callbacks = []

    def _created(self, user):
        """Generate and store all needed data.

        Storage data used:
            password (encryption_string): Encrypted version of the generated password used by
                encrypt/decrypt.
            verify-clear : Clear text version of the verification string.
            verify-crypt : Encrypted version of the verification string.
                Encrypted with self.key.
        """
        super(PasswordKey, self)._created(user)
        if self.password == None:
            raise errors.SiptrackError('invalid password in password key object')
        if len(self.password) > 32:
            raise errors.SiptrackError('password keys > 32 bytes not permitted')
        password = PaddedPassword(self.password, AES.block_size)
        self._encryption_string.set(self._encrypt(password.padded, self._generateString(32)))
        self._verify_clear.set(self._generateString(32))
        self._verify_crypt.set(self._encrypt(password.padded, self._verify_clear.get()))
        self.password = None

    def _loaded(self, data = None):
        """Load data from storage."""
        super(PasswordKey, self)._loaded(data)
        if data != None:
            self._encryption_string.preload(data)
            self._verify_clear.preload(data)
            self._verify_crypt.preload(data)

    def _generateString(self, length):
        """Generate a random string of length characters."""
        ret = ''.join([chr(random.randint(0, 255)) for n in range(length)])
        return ret

    def _encrypt(self, password, dec_string):
        """Encrypt a string, no padding is performed.

        Encrypts the plain text string dec_string with key.
        key and dec_string must be padded to 16 multiples of 16 bytes.
        """
        aesobj = AES.new(password, AES.MODE_ECB)
        enc_string = aesobj.encrypt(dec_string)
        return enc_string

    def encrypt(self, dec_string, pk_password = None, user = None):
        """Encrypt dec_string with the PasswordKey."""
        pk_enc_string = self.getEncryptionString(pk_password, user)
        pk_enc_string = PaddedPassword(pk_enc_string, AES.block_size)
        dec_string = PaddedPassword(dec_string, AES.block_size)
        enc_string = self._encrypt(pk_enc_string.padded, dec_string.padded)
        return (enc_string, str(dec_string.pad_len))

    def _decrypt(self, password, enc_string):
        """Decrypt a string, no padding is performed.

        Decrypts the encrypted string enc_string with key.
        key and enc_string must be padded to 16 multiples of 16 bytes.
        """
        aesobj = AES.new(password, AES.MODE_ECB)
        dec_string = aesobj.decrypt(enc_string)
        return dec_string

    def decrypt(self, enc_string, pad_len, pk_password = None, user = None):
        """Decrypt a string encrypted with the PasswordKey.

        Padding is removed as necessary.
        """
        pk_enc_string = self.getEncryptionString(pk_password, user)
        pk_enc_string = PaddedPassword(pk_enc_string, AES.block_size)
        dec_string = self._decrypt(pk_enc_string.padded, enc_string)
        pad_len = int(pad_len)
        if pad_len > 0:
            dec_string = dec_string[:-pad_len]
        return dec_string

    def isValidPassword(self, password):
        """Check that a password string is valid for this password key."""
        if password is None:
            return False
        password = PaddedPassword(password, AES.block_size)
        verify_crypt = self._encrypt(password.padded, self._verify_clear.get())
        if verify_crypt == self._verify_crypt.get():
            return True
        return False

    def canEncryptDecrypt(self, password = None, user = None):
        ret = False
        if self.isValidPassword(password):
            ret = True
        elif self.getUserEncryptionString(user):
            ret = True
        return ret

    def changePassword(self, old_password, new_password):
        """Change the password for an existing PasswordKey.

        This will change the password used in an existing PasswordKey.
        """
        if new_password == None:
            raise errors.SiptrackError('invalid password in password key object')
        if len(new_password) > 32:
            raise errors.SiptrackError('password keys > 32 bytes not permitted')
        if not self.isValidPassword(old_password):
            raise errors.SiptrackError('invalid password')
        old_password = PaddedPassword(old_password, AES.block_size)
        new_password = PaddedPassword(new_password, AES.block_size)
        enc_string = self._decrypt(old_password.padded, self._encryption_string.get())
        self._encryption_string.set(self._encrypt(new_password.padded, enc_string))
        self._verify_crypt.set(self._encrypt(new_password.padded, self._verify_clear.get()))

    def getLocalEncryptionString(self, password):
        """Get the password keys locally stored encryption string.

        This requires a password to decrypt to be useful.
        """
        if not self.isValidPassword(password):
            raise errors.SiptrackError('invalid password key password')
        password = PaddedPassword(password, AES.block_size)
        enc_string = self._decrypt(password.padded, self._encryption_string.get())
        return enc_string

    def getUserEncryptionString(self, user):
        """Get a password keys encryption string from a subkey.

        Checks a users subkeys and tried to get the encryption string
        from there.
        """
        ret = None
        if user:
            ret = user.getSubkeyEncryptionStringForPasswordKey(self)
        return ret

    def getEncryptionString(self, password = None, user = None):
        """Try to get a password keys encryption string.

        This is the string that is used to encrypt Password object passwords.
        It is encrypted with the password keys password and must as such be
        decrypted before it can be used.
        It can also be fetched from a users subkey.
        This method tries both methods.
        """
        ret = None
        if password is None and user is None:
            raise errors.SiptrackError('no password or user given in getEncryptionString')
        if password:
            ret = self.getLocalEncryptionString(password)
        if user and not ret:
            ret = self.getUserEncryptionString(user)
        if ret is None:
            raise errors.SiptrackError('unable to obtain password key encryption string')
        return ret

class SubKey(treenodes.BaseNode):
    """A subkey is is used to give a user access to a password key.
    
    It is automatically created when a user connects to the password key
    and is located beneath the user in the tree.

    A subkey takes a password keys password (the string it uses to encrypt
    passwords) and stores it locally in
    a password node. The password node is in turn protected by
    a password key of its own, that uses the users password for
    encryption. It's passwords and keys all the way down!
    """
    class_id = 'SK'
    class_name = 'subkey'

    def __init__(self, oid, branch, password_key = None, sk_password = None,
            pk_password = None):
        super(SubKey, self).__init__(oid, branch)
        self._password_key = storagevalue.StorageNode(self, 'password-key',
                password_key)
        self._int_password = None
        self.sk_password = sk_password
        self.pk_password = pk_password

    def _created(self, user):
        super(SubKey, self)._created(user)
        enc_string = self.password_key.getLocalEncryptionString(self.pk_password)
        self._password_key.commit()
        int_password_key = self.add(user, 'password key', self.sk_password)
        self._int_password = self.add(user, 'password', enc_string,
                int_password_key, unicode = False,
                pk_password = self.sk_password)
        self.sk_password = None
        self.pk_password = None

    def _loaded(self, data = None):
        """Load data from storage."""
        super(SubKey, self)._loaded(data)
        self._password_key.preload(data)
        self._int_password = list(self.listChildren(include = ['password']))[0]
        self._int_password.unicode = False

    def getEncryptionString(self, password):
        """Return the subkey encryption string.

        This is the same encryption string that is used by the password
        key the subkey belongs to.
        """
        p = self._int_password.getPassword(pk_password = password, user = None)
        return p

    def changePassword(self, old_password, new_password):
        self._int_password.password_key.changePassword(old_password, new_password)

    def _get_password_key(self):
        return self._password_key.get()
    def _set_password_key(self, val):
        self._password_key.set(val)
    password_key = property(_get_password_key, _set_password_key)

class PaddedPassword(object):
    """Given a string, pads it to the nearest multiple of then block_size."""
    def __init__(self, password, block_size):
        self.password = password
        self.block_size = block_size
        self.padded, self.pad_len = self.pad(self.password, block_size)

    def pad(self, padstr, block_size):
        """Pad a string to the closest multiple of block_size."""
        padstrlen = len(padstr)
        padto = (padstrlen / block_size + 1) * block_size
        padlen = padto - padstrlen
        if padlen == 16:
            # Empty keys aren't permitted.
            if padstrlen != 0:
                padlen = 0
        padstr = padstr + '0' * padlen
        return (padstr, padlen)

class PublicKey(treenodes.BaseNode):
    class_id = 'PUK'
    class_name = 'public key'
    keysize = 1024

    def __init__(self, oid, branch, password_key = None, pk_password = None):
        super(PublicKey, self).__init__(oid, branch)
        self._public_key = storagevalue.StorageText(self, 'public-key', None)
        self._private_key = storagevalue.StorageValue(self, 'private-key', None)
        self._password_key = storagevalue.StorageNode(self, 'password-key',
                password_key)
        self.pk_password = pk_password

    def _created(self, user):
        super(PublicKey, self)._created(user)
        pk_password = self.pk_password
        self.pk_password = None
        self._password_key.commit()
        keypair = self._generateKeypair()
        self._public_key.value = keypair.publickey().exportKey()
        self._public_key.commit()
        self._private_key.value = self._encryptPrivateKey(keypair.exportKey(), pk_password, user)
        self._private_key.commit()

    def _loaded(self, data = None):
        """Load data from storage."""
        super(PublicKey, self)._loaded(data)
        self._public_key.preload(data)
        self._private_key.preload(data)

    def _getPassword(self, password, user):
        ret = None
        if password:
            ret = password
        elif user:
            ret = user.password
        return ret

    def _getRNG(self):
        return Random.new().read

    def _generateKeypair(self):
        rng = self._getRNG()
        rsakey = RSA.generate(self.keysize, rng)
        return rsakey

    def _encryptPrivateKey(self, keystring, password = None, user = None):
        password_key = self._password_key.get()
        pwdata = password_key.encrypt(keystring, password)
        return pwdata

    def _decryptPrivateKey(self, password = None, user = None):
        password_key = self._password_key.get()
        pwdata = self._private_key.get()
        keystring = password_key.decrypt(pwdata[0], pwdata[1], password, user)
        return keystring

    def getPublicKey(self):
        keypair = RSA.importKey(self._public_key.get())
        return keypair

    def getPrivateKey(self, password = None, user = None):
        private_key = self._decryptPrivateKey(password, user)
        keypair = RSA.importKey(private_key)
        return keypair

    def encrypt(self, s):
        keypair = self.getPublicKey()
        return keypair.encrypt(s, None)

    def decrypt(self, s, password = None, user = None):
        keypair = self.getPrivateKey(password, user)
        return keypair.decrypt(s)

class PendingSubKey(treenodes.BaseNode):
    class_id = 'PSK'
    class_name = 'pending subkey'

    def __init__(self, oid, branch, password_key = None, pk_password = None, public_key = None):
        super(PendingSubKey, self).__init__(oid, branch)
        self._password_key = storagevalue.StorageNode(self, 'password-key',
                password_key)
        self._public_key = storagevalue.StorageNode(self, 'public-key',
                public_key)
        self._pk_password = storagevalue.StorageValue(self, 'pk-password',
                pk_password)

    def _created(self, user):
        super(PendingSubKey, self)._created(user)
        self._password_key.commit()
        self._public_key.commit()
        self._pk_password.value = self._public_key.get().encrypt(self._pk_password.value)
        self._pk_password.commit()

    def _loaded(self, data = None):
        """Load data from storage."""
        super(PendingSubKey, self)._loaded(data)
        self._password_key.preload(data)
        self._public_key.preload(data)
        self._pk_password.preload(data)

    def connectPasswordKey(self, user, user_password, remove_self = True):
        password_key = self._password_key.get()
        public_key = self._public_key.get()
        pk_password = self._pk_password.get()
        pk_password = public_key.decrypt(pk_password, user_password, user)
        user.add(None, 'subkey', password_key, user_password, pk_password)
        if remove_self:
            self.remove(recursive=True)

    def _get_password_key(self):
        return self._password_key.get()
    def _set_password_key(self, val):
        self._password_key.set(val)
    password_key = property(_get_password_key, _set_password_key)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(PasswordTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Password)
o.registerChild(PasswordKey)
o.registerChild(PasswordCategory)
o.registerChild(permission.Permission)

o = object_registry.registerClass(PasswordCategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Password)
o.registerChild(permission.Permission)
o.registerChild(PasswordCategory)

o = object_registry.registerClass(Password)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(PasswordKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(SubKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Password)
o.registerChild(PasswordKey)

o = object_registry.registerClass(PublicKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(PendingSubKey)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

