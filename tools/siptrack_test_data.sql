-- MySQL dump 10.16  Distrib 10.1.21-MariaDB, for Linux (x86_64)
--
-- Host: 172.17.0.2    Database: 172.17.0.2
-- ------------------------------------------------------
-- Server version	10.1.22-MariaDB-1~jessie

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `associations`
--

DROP TABLE IF EXISTS `associations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `associations` (
  `self_oid` varchar(16) NOT NULL,
  `other_oid` varchar(16) NOT NULL,
  PRIMARY KEY (`self_oid`,`other_oid`),
  KEY `associations_self_oid_idx` (`self_oid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `associations`
--

LOCK TABLES `associations` WRITE;
/*!40000 ALTER TABLE `associations` DISABLE KEYS */;
/*!40000 ALTER TABLE `associations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `device_config_data`
--

DROP TABLE IF EXISTS `device_config_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `device_config_data` (
  `oid` varchar(16) NOT NULL,
  `data` mediumblob,
  `timestamp` int(11) NOT NULL,
  PRIMARY KEY (`oid`,`timestamp`),
  KEY `device_config_data_oid_idx` (`oid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `device_config_data`
--

LOCK TABLES `device_config_data` WRITE;
/*!40000 ALTER TABLE `device_config_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `device_config_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `idmap`
--

DROP TABLE IF EXISTS `idmap`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `idmap` (
  `parent_oid` varchar(16) DEFAULT NULL,
  `oid` varchar(16) NOT NULL,
  `class_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`oid`),
  KEY `idmap_oid_idx` (`oid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `idmap`
--

LOCK TABLES `idmap` WRITE;
/*!40000 ALTER TABLE `idmap` DISABLE KEYS */;
INSERT INTO `idmap` VALUES ('ROOT','0','VT'),('0','1','UM'),('99','100','CA'),('97','101','CA'),('92','102','TMPLRULETEXT'),('102','103','CA'),('102','104','CA'),('104','105','CA'),('102','106','CA'),('92','107','TMPLRULETEXT'),('107','108','CA'),('107','109','CA'),('107','110','CA'),('107','111','CA'),('53','115','DTMPL'),('115','116','CA'),('115','117','CA'),('92','118','CA'),('115','119','CA'),('115','120','TMPLRULETEXT'),('120','121','CA'),('120','122','CA'),('120','123','CA'),('120','124','CA'),('124','125','CA'),('120','126','CA'),('115','127','TMPLRULETEXT'),('127','128','CA'),('127','129','CA'),('129','130','CA'),('127','131','CA'),('53','132','DTMPL'),('132','133','CA'),('132','134','CA'),('132','135','TMPLRULETEXT'),('135','136','CA'),('135','137','CA'),('137','138','CA'),('135','139','CA'),('53','140','DC'),('140','141','CA'),('48','142','NT'),('142','143','CA'),('48','144','NT'),('144','145','CA'),('1','2','CA'),('1','3','U'),('3','4','PK'),('0','48','V'),('48','49','NT'),('4','5','CA'),('49','50','CA'),('48','51','NT'),('51','52','CA'),('48','53','DT'),('53','54','CA'),('48','55','PT'),('55','56','CA'),('55','57','PK'),('57','58','CA'),('48','59','CNT'),('3','6','PUK'),('59','60','CA'),('59','61','CA'),('53','62','DTMPL'),('62','63','CA'),('62','64','CA'),('62','65','CA'),('62','66','TMPLRULEPASSWORD'),('62','67','TMPLRULEFIXED'),('62','68','TMPLRULEFIXED'),('53','69','DTMPL'),('6','7','CA'),('69','70','CA'),('69','71','CA'),('69','72','CA'),('69','73','TMPLRULEFIXED'),('69','74','TMPLRULEFIXED'),('53','75','DTMPL'),('75','76','CA'),('75','77','CA'),('75','78','CA'),('75','79','TMPLRULEBOOL'),('75','80','TMPLRULESUBDEV'),('53','81','DTMPL'),('81','82','CA'),('81','83','CA'),('81','84','CA'),('81','85','TMPLRULETEXT'),('81','86','TMPLRULEFIXED'),('48','87','CA'),('53','88','DC'),('88','89','CA'),('53','92','DTMPL'),('92','93','CA'),('92','94','CA'),('92','95','TMPLRULEFIXED'),('95','96','CA'),('92','97','TMPLRULETEXT'),('97','98','CA'),('97','99','CA');
/*!40000 ALTER TABLE `idmap` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nodedata`
--

DROP TABLE IF EXISTS `nodedata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nodedata` (
  `oid` varchar(16) NOT NULL,
  `name` varchar(64) NOT NULL,
  `datatype` varchar(16) DEFAULT NULL,
  `data` blob,
  PRIMARY KEY (`oid`,`name`),
  KEY `nodedata_oid_idx` (`oid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nodedata`
--

LOCK TABLES `nodedata` WRITE;
/*!40000 ALTER TABLE `nodedata` DISABLE KEYS */;
INSERT INTO `nodedata` VALUES ('0','user_manager','pickle','S\'1\'\n.'),('1','ctime','pickle','I1493230702\n.'),('100','attr-name','pickle','S\'exclude\'\np1\n.'),('100','attr-type','pickle','S\'bool\'\np1\n.'),('100','attr-value','pickle','I1\n.'),('100','ctime','pickle','I1493231180\n.'),('101','attr-name','pickle','S\'priority\'\np1\n.'),('101','attr-type','pickle','S\'int\'\np1\n.'),('101','attr-value','pickle','I1\n.'),('101','ctime','pickle','I1493231180\n.'),('102','attr name','pickle','S\'description\'\np1\n.'),('102','ctime','pickle','I1493231210\n.'),('102','versions','pickle','I1\n.'),('103','attr-name','pickle','S\'important\'\np1\n.'),('103','attr-type','pickle','S\'bool\'\np1\n.'),('103','attr-value','pickle','I1\n.'),('103','ctime','pickle','I1493231210\n.'),('104','attr-name','pickle','S\'description\'\np1\n.'),('104','attr-type','pickle','S\'text\'\np1\n.'),('104','attr-value','pickle','S\'Device description\'\np1\n.'),('104','ctime','pickle','I1493231211\n.'),('105','attr-name','pickle','S\'exclude\'\np1\n.'),('105','attr-type','pickle','S\'bool\'\np1\n.'),('105','attr-value','pickle','I1\n.'),('105','ctime','pickle','I1493231211\n.'),('106','attr-name','pickle','S\'priority\'\np1\n.'),('106','attr-type','pickle','S\'int\'\np1\n.'),('106','attr-value','pickle','I2\n.'),('106','ctime','pickle','I1493231211\n.'),('107','attr name','pickle','S\'notes\'\np1\n.'),('107','ctime','pickle','I1493231231\n.'),('107','versions','pickle','I5\n.'),('108','attr-name','pickle','S\'wikitext\'\np1\n.'),('108','attr-type','pickle','S\'bool\'\np1\n.'),('108','attr-value','pickle','I1\n.'),('108','ctime','pickle','I1493231231\n.'),('109','attr-name','pickle','S\'large\'\np1\n.'),('109','attr-type','pickle','S\'bool\'\np1\n.'),('109','attr-value','pickle','I1\n.'),('109','ctime','pickle','I1493231231\n.'),('110','attr-name','pickle','S\'important\'\np1\n.'),('110','attr-type','pickle','S\'bool\'\np1\n.'),('110','attr-value','pickle','I1\n.'),('110','ctime','pickle','I1493231231\n.'),('111','attr-name','pickle','S\'priority\'\np1\n.'),('111','attr-type','pickle','S\'int\'\np1\n.'),('111','attr-value','pickle','I11\n.'),('111','ctime','pickle','I1493231231\n.'),('115','ctime','pickle','I1493231275\n.'),('115','inheritance_only','pickle','I00\n.'),('115','inherited','pickle','(lp1\nS\'92\'\np2\na.'),('116','attr-name','pickle','S\'device_creation\'\np1\n.'),('116','attr-type','pickle','S\'bool\'\np1\n.'),('116','attr-value','pickle','I1\n.'),('116','ctime','pickle','I1493231275\n.'),('117','attr-name','pickle','S\'name\'\np1\n.'),('117','attr-type','pickle','S\'text\'\np1\n.'),('117','attr-value','pickle','S\'Physical server\'\np1\n.'),('117','ctime','pickle','I1493231275\n.'),('118','attr-name','pickle','S\'description\'\np1\n.'),('118','attr-type','pickle','S\'text\'\np1\n.'),('118','attr-value','pickle','S\'\'\n.'),('118','ctime','pickle','I1493231298\n.'),('119','attr-name','pickle','S\'description\'\np1\n.'),('119','attr-type','pickle','S\'text\'\np1\n.'),('119','attr-value','pickle','S\'\'\n.'),('119','ctime','pickle','I1493231333\n.'),('120','attr name','pickle','S\'location\'\np1\n.'),('120','ctime','pickle','I1493231395\n.'),('120','versions','pickle','I5\n.'),('121','attr-name','pickle','S\'wikitext\'\np1\n.'),('121','attr-type','pickle','S\'bool\'\np1\n.'),('121','attr-value','pickle','I1\n.'),('121','ctime','pickle','I1493231395\n.'),('122','attr-name','pickle','S\'large\'\np1\n.'),('122','attr-type','pickle','S\'bool\'\np1\n.'),('122','attr-value','pickle','I1\n.'),('122','ctime','pickle','I1493231395\n.'),('123','attr-name','pickle','S\'important\'\np1\n.'),('123','attr-type','pickle','S\'bool\'\np1\n.'),('123','attr-value','pickle','I1\n.'),('123','ctime','pickle','I1493231395\n.'),('124','attr-name','pickle','S\'description\'\np1\n.'),('124','attr-type','pickle','S\'text\'\np1\n.'),('124','attr-value','pickle','S\'Physical location\'\np1\n.'),('124','ctime','pickle','I1493231395\n.'),('125','attr-name','pickle','S\'exclude\'\np1\n.'),('125','attr-type','pickle','S\'bool\'\np1\n.'),('125','attr-value','pickle','I1\n.'),('125','ctime','pickle','I1493231395\n.'),('126','attr-name','pickle','S\'priority\'\np1\n.'),('126','attr-type','pickle','S\'int\'\np1\n.'),('126','attr-value','pickle','I10\n.'),('126','ctime','pickle','I1493231395\n.'),('127','attr name','pickle','S\'watts\'\np1\n.'),('127','ctime','pickle','I1493231420\n.'),('127','versions','pickle','I1\n.'),('128','attr-name','pickle','S\'important\'\np1\n.'),('128','attr-type','pickle','S\'bool\'\np1\n.'),('128','attr-value','pickle','I1\n.'),('128','ctime','pickle','I1493231420\n.'),('129','attr-name','pickle','S\'description\'\np1\n.'),('129','attr-type','pickle','S\'text\'\np1\n.'),('129','attr-value','pickle','S\'Power usage\'\np1\n.'),('129','ctime','pickle','I1493231421\n.'),('130','attr-name','pickle','S\'exclude\'\np1\n.'),('130','attr-type','pickle','S\'bool\'\np1\n.'),('130','attr-value','pickle','I1\n.'),('130','ctime','pickle','I1493231421\n.'),('131','attr-name','pickle','S\'priority\'\np1\n.'),('131','attr-type','pickle','S\'int\'\np1\n.'),('131','attr-value','pickle','I10\n.'),('131','ctime','pickle','I1493231421\n.'),('132','ctime','pickle','I1493231455\n.'),('132','inheritance_only','pickle','I00\n.'),('132','inherited','pickle','(lp1\nS\'92\'\np2\na.'),('133','attr-name','pickle','S\'device_creation\'\np1\n.'),('133','attr-type','pickle','S\'bool\'\np1\n.'),('133','attr-value','pickle','I1\n.'),('133','ctime','pickle','I1493231455\n.'),('134','attr-name','pickle','S\'name\'\np1\n.'),('134','attr-type','pickle','S\'text\'\np1\n.'),('134','attr-value','pickle','S\'Virtual server\'\np1\n.'),('134','ctime','pickle','I1493231455\n.'),('135','attr name','pickle','S\'hypervisor\'\np1\n.'),('135','ctime','pickle','I1493231476\n.'),('135','versions','pickle','I1\n.'),('136','attr-name','pickle','S\'important\'\np1\n.'),('136','attr-type','pickle','S\'bool\'\np1\n.'),('136','attr-value','pickle','I1\n.'),('136','ctime','pickle','I1493231476\n.'),('137','attr-name','pickle','S\'description\'\np1\n.'),('137','attr-type','pickle','S\'text\'\np1\n.'),('137','attr-value','pickle','S\'Type of hypervisor\'\np1\n.'),('137','ctime','pickle','I1493231476\n.'),('138','attr-name','pickle','S\'exclude\'\np1\n.'),('138','attr-type','pickle','S\'bool\'\np1\n.'),('138','attr-value','pickle','I1\n.'),('138','ctime','pickle','I1493231476\n.'),('139','attr-name','pickle','S\'priority\'\np1\n.'),('139','attr-type','pickle','S\'int\'\np1\n.'),('139','attr-value','pickle','I10\n.'),('139','ctime','pickle','I1493231476\n.'),('140','ctime','pickle','I1493231521\n.'),('141','attr-name','pickle','S\'name\'\np1\n.'),('141','attr-type','pickle','S\'text\'\np1\n.'),('141','attr-value','pickle','S\'Virtual servers\'\np1\n.'),('141','ctime','pickle','I1493231521\n.'),('142','ctime','pickle','I1493231536\n.'),('142','network-protocol','pickle','S\'ipv4\'\np1\n.'),('143','attr-name','pickle','S\'name\'\np1\n.'),('143','attr-type','pickle','S\'text\'\np1\n.'),('143','attr-value','pickle','S\'192.168.22.0/24\'\np1\n.'),('143','ctime','pickle','I1493231536\n.'),('144','ctime','pickle','I1493231566\n.'),('144','network-protocol','pickle','S\'ipv4\'\np1\n.'),('145','attr-name','pickle','S\'name\'\np1\n.'),('145','attr-type','pickle','S\'text\'\np1\n.'),('145','attr-value','pickle','S\'192.168.21.0/24\'\np1\n.'),('145','ctime','pickle','I1493231566\n.'),('2','attr-name','pickle','S\'name\'\np1\n.'),('2','attr-type','pickle','S\'text\'\np1\n.'),('2','attr-value','pickle','S\'default user manager\'\np1\n.'),('2','ctime','pickle','I1493230702\n.'),('3','administrator','pickle','I01\n.'),('3','ctime','pickle','I1493230702\n.'),('3','password','pickle','S\'d033e22ae348aeb5660fc2140aec35850c4da997\'\np1\n.'),('3','username','pickle','S\'admin\'\np1\n.'),('4','ctime','pickle','I1493230766\n.'),('4','password','pickle','S\'\\xd6\\xf2\\xf2u\\x01f\\xe07\\xb0\\xb4\\x0f\\x9av\\xe6\\x8a\\x12xw\\xef\\xae\\xccIZ\\xe4\\x14\\xcc\\xb1\\x8a\\xab\\x14\\xe0A\'\np1\n.'),('4','verify-clear','pickle','S\'P\\xbcq\\xba\\\\?\\xd6\\x9d1+\"K\\x83\\x01\\xdf\\xf8\\xcb\\x97-\\xd5a\\x80$\\x9a^P\\xac\\xd3\\x94x\\x80I\'\np1\n.'),('4','verify-crypt','pickle','S\'\\xda\\xf4\\xe2\\x02\\xfepD\\x03\\t#~w\\\\\\x81\\x16e\\x00\\xb8o\\xfd\\xccqL\\x0b\\xc7\\x126\\xa3\\x1c\\xf39\\xe6\'\np1\n.'),('48','ctime','pickle','I1493230809\n.'),('49','ctime','pickle','I1493230809\n.'),('49','network-protocol','pickle','S\'ipv4\'\np1\n.'),('5','attr-name','pickle','S\'default\'\np1\n.'),('5','attr-type','pickle','S\'bool\'\np1\n.'),('5','attr-value','pickle','I1\n.'),('5','ctime','pickle','I1493230766\n.'),('50','attr-name','pickle','S\'name\'\np1\n.'),('50','attr-type','pickle','S\'text\'\np1\n.'),('50','attr-value','pickle','S\'ipv4\'\np1\n.'),('50','ctime','pickle','I1493230809\n.'),('51','ctime','pickle','I1493230809\n.'),('51','network-protocol','pickle','S\'ipv6\'\np1\n.'),('52','attr-name','pickle','S\'name\'\np1\n.'),('52','attr-type','pickle','S\'text\'\np1\n.'),('52','attr-value','pickle','S\'ipv6\'\np1\n.'),('52','ctime','pickle','I1493230809\n.'),('53','ctime','pickle','I1493230809\n.'),('54','attr-name','pickle','S\'name\'\np1\n.'),('54','attr-type','pickle','S\'text\'\np1\n.'),('54','attr-value','pickle','S\'default\'\np1\n.'),('54','ctime','pickle','I1493230809\n.'),('55','ctime','pickle','I1493230809\n.'),('56','attr-name','pickle','S\'name\'\np1\n.'),('56','attr-type','pickle','S\'text\'\np1\n.'),('56','attr-value','pickle','S\'default\'\np1\n.'),('56','ctime','pickle','I1493230809\n.'),('57','ctime','pickle','I1493230809\n.'),('57','password','pickle','S\"\\x93[[\'\\xcc\\xda-/\\x97\\xf04\\xfd\\x8d\\xf6c0\\xbe\\x8e\\xa2f\\x8b\\xb1u3N\\xc1\\xa7+)\\x80\\xdd%\"\np1\n.'),('57','verify-clear','pickle','S\'\\xaf\\xf2\\x0f\\x83O\\xba\\xddU\\xbd!\\xefE\\xb6\\xe1\\xed\\x08[=\\xadTj\\xc1\\x80\\x19\\x10\\x13Q\\x8d\\xf5X\\x1c\\x05\'\np1\n.'),('57','verify-crypt','pickle','S\'\\xaf\\xf6\\x97I\\xcbL\\xae\\xfd\\n\\x91\\t+\\x11T\\xe7\\x1c!\\xa2#\\xf1jS\\xedP\\xd7C{\\xbd\\x83\\x85\\x06Z\'\np1\n.'),('58','attr-name','pickle','S\'description\'\np1\n.'),('58','attr-type','pickle','S\'text\'\np1\n.'),('58','attr-value','pickle','S\'Sample password key, password: password\'\np1\n.'),('58','ctime','pickle','I1493230809\n.'),('59','ctime','pickle','I1493230809\n.'),('59','value','pickle','I1\n.'),('6','ctime','pickle','I1493230766\n.'),('6','password-key','pickle','S\'4\'\n.'),('6','private-key','pickle','(S\'\\x1d\\xa1u\\xd7.\\x8d\\x9c\\xf4gcj\\x07,\\x0f\\xf8\\xc5O\\xf7Z7\\x85N\\xb5\\xda\\x8dF\\x15\\x1a\\xef\\x9aVL\\x84v\\xea\\\'\\x80\\xea\\x1ao\\xc8\\xbeW\\x95\\xbc\\xc4\\xd7!\\x88q\\x1f\\x08\\xb8F\\xb4~\\x98\\xa7\\x12\\x1bI\\xa1\\xff\\xb54\\x14\\xbc`\\x07\\\'\\x0b\\xe4q\\xb426vA&#\\xb8\\xc9\\xcf\\xe4\\x84\\x1f2qo\\x15\\xfc\\xfc).\\xa7\\xcc\\x9e\\xe3\\xc7\\xf9\\x8bZ\\xaeE7\\xfc\\xe1\\x9b\\xf8\\xee\\xf9\\xdf\\xfb^xHP\\xdb\"\\xe4\\xb4L\\xe0\\xfc\\x97\\x9a\\r|\\xcd$t\\xa4\\xc5\\xaf0{\\xe4\\xd9\\xf7\\xe8\\\'\\xc4\\x1c\\x81\\xe6\\xa0$\\xa7e\\xd4\\x03\\xb6qh^\\xf3!\\xeac\\x86l\\x13C\\xb1Q1\\x93\\xfb\\xf7\\xfa\\xaag\\xf2LG\\x1f\\xe5\\x95k\\xcc%V\\xac\\x16\\x88/\\xdf\\x80o\\x97u\\xa7\\xd5\\xf7\\xa9\\xac\\n3\\x9f\\xde\\xae\\xf5m\\xab\\xec\\xaewn\\xd7\\x9c\\xe6\\xd5DK\\xe1\\xc4DOD\\x91H\\x86\\x9cu\\x91\\x8al\\x926l\\x17oko\\x84\\x9e\\xbe\\xebx\\x96\\xbau\\xcf\\x90\\x9a\\xb8\\xa1u\\xb1\\xf7bY=\\x7f\\x866J\\xc3<\\xa8\\x06tZ\\x16\\xc0\\xad\\x8a<Z\\xf5I\\xfa\\xbd\\x7fh\\xc4\\xaa\\x07\\x81O\\xa9\\xff\\x7f;\\xcb\\x82\\\'p\\x85B\\xf9F\\xc7T\\x9a \\x85\\x84\\xcdr\\x07\\xffFj\\xa4\\xf7f(\\xeastT/\\xd3,\\xe1&\\xd3\\x82~\\xd6\\x8efz;\\xbf6\\xe3 \\xf4\\xff.0I\\xb9\\xd0*dq\\xaev\\xf5\\x96\\x12\\xd6\\xe7l{,a\\xe3B\\x83\\xda=U\\xfef\\x8eA\\xec\\xcc\\xb1\\xb31\\x87S\\xf5y\\xa76<|b\\xdc$\\x9a\\x96\\x15\\x15\\xcdI\\x9f\\xa8\\xe2\\x056,\\xa9\\x87g%~\\x9c~n\\x1d\\x94\\xdbp\\xc5\\x1eQqv\\x84\\x0cu\\xda\\xa6\\xa9;\\xab\\x8f(#\\x01\\xda\\xfc\\xdd\\\'\\x077\\x15\\x99\\x07\\x0f\\x06\\xdd8I\\xbe\\xe0E\\x06Tnm\\xd4\\x0b\\x0f\\xb0\\xf87=\\xf6oG\\x1c\\xc0\\x1f\\x1c\\xbaO\\x06_\\x1fX \\xa2\\xa0\\x97\\xd6\\xa7\\xff\\x7f\\xd1\\x8f\\x9f\\xbc(\\x8f0=\\xaa\\x97:\\xa8\\xd9\\x1e\\x91\\xb6\\x96\\x90e\\x1fG\\x06z\\x7f\\xadc1\\xc8\\xfazL\\x8f\\xbe\\xff\\xafQ\\xa0\\x85E<\\xb3i\\x7fFD\\xa6\\x1e\\xec\\xbd\\xf8m~W\\xe2/\\xf4\\x93\\xc2Q^\\xaa)\\xd5$\\xe9\\x1f\\xe4\\x1f\\x81\\x18W\\xdf\\x88\\xc9\\xf4\\r\\xe0\\x9bG\\x18l\\x00O\\x0f\\xb5\\x128\\x9a+\\xb4\\xe5\\xc9\\xb3~\\xaf\\x81\\xd4\\xce\\xf8\\xcf\\xf4\\xee#P7\\x94\\xc5\\xa6\\xdd\\xb8\\x80\\xd8\\x90\\xa0k1\\xd1\\x87\\xd1#\\xb8\\xccW\\xcf\\x03\\xf7)\\xc3\\x7fl-\\x9a\\xd0\\xfe+DG~\\xfb\\x86&\\xf1\\x9a\\r\\xce\\xf2\\xa0\\x9f\\xd4&-\\x88\\xc1\\x9c\\xe9\\xc8\\xa4p5v\\xa1\\x06\\x1f\\x0c.\\x99y0\\xa7\\xf3Z\\xb1\\xc7\\ta\\\'\\x16\\xd9\\xe4d\\xfc\\x87\\xbfpi\\x05e\\x9d\\xf8\\xf2h\\x88\\xf2\\xa0\\t\\x1aH\\x97\\xf2\\x88\\xbde\\xb4\\x8f\\xaeO\\xa3j\\\'\\xa3\\x1e\\xa2\\x85\\xc8\\xf5?\\x17L\\x90\\xe2\\x91\\x11\\xb8\\xcc\\x82\\xbcq\\x8e\\xcd\\x87\\xd0.v\\x1d\\xdb\\xd81\\xdfH\\xff@\\x92\\\\\\xa6Iiy\\xc7/\\xd4\\xbc\\xa7o\\\\\\xad7\\xa4\\xe1\\xc5\\xe4\\xc6|o\\x99r\\xf2\\xdd\\xf5\\xe1gFY\\xf4FuK\\xf1c\\x1e@\\xf8Q!\\xc1\\x84\\xb3l\\xc7\\x8dT\\xf7\\x00\\r\\xe8^\\xe5{\\x05\\xf6\\xe5\\xba\\x16(\\xd6\\x95g~5\\x99\\x0cv\\x07\\xe9\\xbf\\xbf\\xfb`oG\\x80\\xdb\\xbc\\xab~\\x7f\\n@\\xc0\\xd9\\xca\\x12\\x17\\xb6\\xe86A\\x05/\\x96\\xa8\\xab\\xbfc\\x0c]\\xbd\\xdb\\\',\\xa2\\xf0\\xcd\\xf7\\xab=\\xc0\\x85n8\\x01R\\x9b\\x14\\xaar\\x98\\x02RV\\x8d\\xb9\\x15\\xc3\\xd1\\xac\\xc5\\x8f\\xf9\\x91X\\x16J\\xf0\\xba\\xf8\\xdb\\x91X\\xd73Z\\xfa\\xa9\\xfe\\n\\xf0\\xd1\\xcf\\x9c\\x9e\\xf13\\xe5\\x06\\x17lb\\x1d6\\xa8\\xfd\\xd67\\x0b\\xca\\x13X\\xc7E\\xfaa7\\xf3\\nY\\x93\\xd4Y{\\xb7\'\nS\'10\'\ntp1\n.'),('6','public-key','pickle','S\'-----BEGIN PUBLIC KEY-----\\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCwrpWaz2w3QXYuGyW9TN/IlYJa\\nyFoXCHj9riDqocJWFmfVmvZ1CMO3kPAfF+r7ryNRY6ULViXbNxAFL+/BzsjfbS6J\\nUYJt4tWOjwR1QdH+gOvP3iKOjq1GLIe16xKUNbk1famNWU9hgJewMLaO/ow7p42S\\n1mq83b6o6mXjhFv8eQIDAQAB\\n-----END PUBLIC KEY-----\'\np1\n.'),('60','attr-name','pickle','S\'name\'\np1\n.'),('60','attr-type','pickle','S\'text\'\np1\n.'),('60','attr-value','pickle','S\'server-counter\'\np1\n.'),('60','ctime','pickle','I1493230809\n.'),('61','attr-name','pickle','S\'description\'\np1\n.'),('61','attr-type','pickle','S\'text\'\np1\n.'),('61','attr-value','pickle','S\'Server counter\'\np1\n.'),('61','ctime','pickle','I1493230809\n.'),('62','ctime','pickle','I1493230809\n.'),('62','inheritance_only','pickle','I00\n.'),('62','inherited','pickle','(lp1\n.'),('63','attr-name','pickle','S\'description\'\np1\n.'),('63','attr-type','pickle','S\'text\'\np1\n.'),('63','attr-value','pickle','S\'Sample server template\'\np1\n.'),('63','ctime','pickle','I1493230809\n.'),('64','attr-name','pickle','S\'name\'\np1\n.'),('64','attr-type','pickle','S\'text\'\np1\n.'),('64','attr-value','pickle','S\'Server\'\np1\n.'),('64','ctime','pickle','I1493230809\n.'),('65','attr-name','pickle','S\'device_creation\'\np1\n.'),('65','attr-type','pickle','S\'bool\'\np1\n.'),('65','attr-value','pickle','I1\n.'),('65','ctime','pickle','I1493230810\n.'),('66','ctime','pickle','I1493230810\n.'),('66','description','pickle','S\'default user\'\np1\n.'),('66','key','pickle','N.'),('66','username','pickle','S\'admin\'\np1\n.'),('67','attr name','pickle','S\'class\'\np1\n.'),('67','ctime','pickle','I1493230810\n.'),('67','value','pickle','S\'server\'\np1\n.'),('67','variable expansion','pickle','I00\n.'),('67','versions','pickle','I1\n.'),('68','attr name','pickle','S\'name\'\np1\n.'),('68','ctime','pickle','I1493230810\n.'),('68','value','pickle','S\'server-%04d counter:server-counter\'\np1\n.'),('68','variable expansion','pickle','I01\n.'),('68','versions','pickle','I1\n.'),('69','ctime','pickle','I1493230810\n.'),('69','inheritance_only','pickle','I00\n.'),('69','inherited','pickle','(lp1\n.'),('7','attr-name','pickle','S\'default\'\np1\n.'),('7','attr-type','pickle','S\'bool\'\np1\n.'),('7','attr-value','pickle','I1\n.'),('7','ctime','pickle','I1493230767\n.'),('70','attr-name','pickle','S\'description\'\np1\n.'),('70','attr-type','pickle','S\'text\'\np1\n.'),('70','attr-value','pickle','S\'Rack unit subdevice template.\'\np1\n.'),('70','ctime','pickle','I1493230810\n.'),('71','attr-name','pickle','S\'name\'\np1\n.'),('71','attr-type','pickle','S\'text\'\np1\n.'),('71','attr-value','pickle','S\'Rack Unit\'\np1\n.'),('71','ctime','pickle','I1493230810\n.'),('72','attr-name','pickle','S\'device_creation\'\np1\n.'),('72','attr-type','pickle','S\'bool\'\np1\n.'),('72','attr-value','pickle','I0\n.'),('72','ctime','pickle','I1493230810\n.'),('73','attr name','pickle','S\'class\'\np1\n.'),('73','ctime','pickle','I1493230810\n.'),('73','value','pickle','S\'rack unit\'\np1\n.'),('73','variable expansion','pickle','I00\n.'),('73','versions','pickle','I1\n.'),('74','attr name','pickle','S\'name\'\np1\n.'),('74','ctime','pickle','I1493230810\n.'),('74','value','pickle','S\'%02d sequence:subdevice\'\np1\n.'),('74','variable expansion','pickle','I01\n.'),('74','versions','pickle','I1\n.'),('75','ctime','pickle','I1493230810\n.'),('75','inheritance_only','pickle','I00\n.'),('75','inherited','pickle','(lp1\n.'),('76','attr-name','pickle','S\'description\'\np1\n.'),('76','attr-type','pickle','S\'text\'\np1\n.'),('76','attr-value','pickle','S\'Create rack units.\'\np1\n.'),('76','ctime','pickle','I1493230810\n.'),('77','attr-name','pickle','S\'name\'\np1\n.'),('77','attr-type','pickle','S\'text\'\np1\n.'),('77','attr-value','pickle','S\'Rack Units\'\np1\n.'),('77','ctime','pickle','I1493230810\n.'),('78','attr-name','pickle','S\'device_creation\'\np1\n.'),('78','attr-type','pickle','S\'bool\'\np1\n.'),('78','attr-value','pickle','I0\n.'),('78','ctime','pickle','I1493230810\n.'),('79','attr name','pickle','S\'reverse-device-sort-order\'\np1\n.'),('79','ctime','pickle','I1493230810\n.'),('79','default value','pickle','I01\n.'),('79','versions','pickle','I1\n.'),('80','ctime','pickle','I1493230810\n.'),('80','device_tmpl','pickle','S\'69\'\np1\n.'),('80','num_devices','pickle','I42\n.'),('80','sequence_offset','pickle','I1\n.'),('81','ctime','pickle','I1493230810\n.'),('81','inheritance_only','pickle','I00\n.'),('81','inherited','pickle','(lp1\nS\'75\'\np2\na.'),('82','attr-name','pickle','S\'description\'\np1\n.'),('82','attr-type','pickle','S\'text\'\np1\n.'),('82','attr-value','pickle','S\'Rack template.\'\np1\n.'),('82','ctime','pickle','I1493230810\n.'),('83','attr-name','pickle','S\'name\'\np1\n.'),('83','attr-type','pickle','S\'text\'\np1\n.'),('83','attr-value','pickle','S\'Rack\'\np1\n.'),('83','ctime','pickle','I1493230810\n.'),('84','attr-name','pickle','S\'device_creation\'\np1\n.'),('84','attr-type','pickle','S\'bool\'\np1\n.'),('84','attr-value','pickle','I1\n.'),('84','ctime','pickle','I1493230810\n.'),('85','attr name','pickle','S\'name\'\np1\n.'),('85','ctime','pickle','I1493230810\n.'),('85','versions','pickle','I1\n.'),('86','attr name','pickle','S\'class\'\np1\n.'),('86','ctime','pickle','I1493230810\n.'),('86','value','pickle','S\'rack\'\np1\n.'),('86','variable expansion','pickle','I00\n.'),('86','versions','pickle','I1\n.'),('87','attr-name','pickle','S\'name\'\np1\n.'),('87','attr-type','pickle','S\'text\'\np1\n.'),('87','attr-value','pickle','S\'Main view\'\np1\n.'),('87','ctime','pickle','I1493230810\n.'),('88','ctime','pickle','I1493230822\n.'),('89','attr-name','pickle','S\'name\'\np1\n.'),('89','attr-type','pickle','S\'text\'\np1\n.'),('89','attr-value','pickle','S\'Home\'\np1\n.'),('89','ctime','pickle','I1493230822\n.'),('92','ctime','pickle','I1493231088\n.'),('92','inheritance_only','pickle','I01\n.'),('92','inherited','pickle','(lp1\n.'),('93','attr-name','pickle','S\'device_creation\'\np1\n.'),('93','attr-type','pickle','S\'bool\'\np1\n.'),('93','attr-value','pickle','I0\n.'),('93','ctime','pickle','I1493231088\n.'),('94','attr-name','pickle','S\'name\'\np1\n.'),('94','attr-type','pickle','S\'text\'\np1\n.'),('94','attr-value','pickle','S\'Server base template\'\np1\n.'),('94','ctime','pickle','I1493231088\n.'),('95','attr name','pickle','S\'class\'\np1\n.'),('95','ctime','pickle','I1493231145\n.'),('95','value','pickle','S\'server\'\np1\n.'),('95','variable expansion','pickle','I00\n.'),('95','versions','pickle','I1\n.'),('96','attr-name','pickle','S\'priority\'\np1\n.'),('96','attr-type','pickle','S\'int\'\np1\n.'),('96','attr-value','pickle','I10\n.'),('96','ctime','pickle','I1493231145\n.'),('97','attr name','pickle','S\'name\'\np1\n.'),('97','ctime','pickle','I1493231180\n.'),('97','versions','pickle','I1\n.'),('98','attr-name','pickle','S\'important\'\np1\n.'),('98','attr-type','pickle','S\'bool\'\np1\n.'),('98','attr-value','pickle','I1\n.'),('98','ctime','pickle','I1493231180\n.'),('99','attr-name','pickle','S\'description\'\np1\n.'),('99','attr-type','pickle','S\'text\'\np1\n.'),('99','attr-value','pickle','S\'Server name\'\np1\n.'),('99','ctime','pickle','I1493231180\n.');
/*!40000 ALTER TABLE `nodedata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `version`
--

DROP TABLE IF EXISTS `version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `version` (
  `version` varchar(100) NOT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `version`
--

LOCK TABLES `version` WRITE;
/*!40000 ALTER TABLE `version` DISABLE KEYS */;
INSERT INTO `version` VALUES ('2');
/*!40000 ALTER TABLE `version` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-04-26 20:34:49
