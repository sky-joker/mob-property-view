# mob-property-view

VMwareのManagement Object(MOB)のPropertyやData Object、Methodを一覧表示するツール

## 必要条件

* python3
* pyvmomi

## インストール

mob-property-viewのインストール

```bash
$ git clone https://github.com/sky-joker/mob-property-view.git
```

実行権限を付与

```bash
$ chmod +x mob-property-view/mob-property-view.py
```

## 使い方

指定可能なManaged Objects

* Datacenter
* ClusterComputeResource
* HostSystem
* Datastore
* Folder
* Network
* DistributedVirtualSwitch
* DistributedVirtualPortgroup
* ResourcePool
* VirtualMachine

ヘルプ

```bash
$ ./mob-property-view.py -h
usage: mob-property-view [-h] --host HOST [--username USERNAME]
                         [--password PASSWORD] --mob
                         {Datacenter,ClusterComputeResource,HostSystem,Datastore,Folder,Network,ResourcePool,VirtualMachine,DistributedVirtualSwitch,DistributedVirtualPortgroup}
                         [--target TARGET [TARGET ...]]
                         [--property property name] [--property-list]
                         [--method-list]

Management ObjectのPropertyやMethod一覧を表示します

optional arguments:
  -h, --help            show this help message and exit
  --host HOST, -vc HOST
                        vCenterのIP又はホスト名
  --username USERNAME, -u USERNAME
                        vCenterのログインユーザー名(default:administrator@vsphere.local)
  --password PASSWORD, -p PASSWORD
                        vCenterのログインユーザーパスワード
  --mob {Datacenter,ClusterComputeResource,HostSystem,Datastore,Folder,Network,ResourcePool,VirtualMachine,DistributedVirtualSwitch,DistributedVirtualPortgroup}
                        取得したい対象のmobを指定
  --target TARGET [TARGET ...], -t TARGET [TARGET ...]
                        MOBの名前(nameプロパティのもの)を指定
  --property property name
                        MOBの表示したい親プロパティを指定
  --property-list, -pl  MOBの親プロパティ一覧を表示
  --method-list, -ml    MOBのメソッド一覧を表示
```

devel(仮想マシン)ののProperty情報を再帰的に取得

```bash
$ ./mob-property-view.py -vc vcenter01.local --mob VirtualMachine -t devel
Password:
---------
| devel |
---------
------------------
| availableField |
------------------
(vim.CustomFieldsManager.FieldDef) []
--------------
| capability |
--------------
(vim.vm.Capability) {
   dynamicType = <unset>,
   dynamicProperty = (vmodl.DynamicProperty) [],
   snapshotOperationsSupported = true,
   multipleSnapshotsSupported = true,
(snip)
```

devel(仮想マシン)のname Propertyを取得

```bash
$ ./mob-property-view.py -vc vcenter01.local --mob VirtualMachine -t devel --property name
Password:
---------
| devel |
---------
--------
| name |
--------
devel
```

devel(仮想マシン)のProperty一覧を取得

```bash
$ ./mob-property-view.py -vc vcenter01.local --mob VirtualMachine -t devel -pl
Password:
---------
| devel |
---------
availableField
capability
config
(snip)
```

devel(仮想マシン)のMethod一覧を取得

```bash
$ ./mob-property-view.py -vc vcenter01.local --mob VirtualMachine -t devel -ml
Password:
---------
| devel |
---------
AcquireMksTicket
AcquireTicket
Answer
(snip)
```

全仮想マシンのname Propertyを取得

```bash
$ ./mob-property-view.py -vc vcenter01.local --mob VirtualMachine --property name
Password:
----------
| centos |
----------
--------
| name |
--------
centos
---------
| devel |
---------
--------
| name |
--------
devel
```

## ライセンス

[MIT](https://github.com/sky-joker/mob-property-view/blob/master/LICENSE.txt)

## 作者

[sky-joker](https://github.com/sky-joker)
