#!/usr/bin/env python3
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
import atexit
import argparse
import re
import types
from getpass import getpass
from collections import defaultdict
__license__ = 'MIT'

def options():
    """
    コマンドラインオプション設定

    :rtype: class
    :return: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog='mob-property-view',
                                     add_help=True,
                                     description='Management ObjectのPropertyやMethod一覧を表示します')
    parser.add_argument('--host', '-vc',
                        type=str, required=True,
                        help='vCenterのIP又はホスト名')
    parser.add_argument('--username', '-u',
                        type=str, default='administrator@vsphere.local',
                        help='vCenterのログインユーザー名(default:administrator@vsphere.local)')
    parser.add_argument('--password', '-p',
                        type=str,
                        help='vCenterのログインユーザーパスワード')
    parser.add_argument('--mob',
                        type=str, required=True,
                        choices=['Datacenter', 'ClusterComputeResource', 'ComputeResource', 'HostSystem',
                        'Datastore', 'Folder', 'Network', 'ResourcePool', 'VirtualMachine',
                        'DistributedVirtualSwitch', 'DistributedVirtualPortgroup'],
                        help='取得したい対象のmobを指定')
    parser.add_argument('--target', '-t',
                        type=str, nargs='+',
                        help='MOBの名前(nameプロパティのもの)を指定')
    parser.add_argument('--property',
                        type=str, metavar='property name',
                        help='MOBの表示したい親プロパティを指定')
    parser.add_argument('--property-list', '-pl',
                        action='store_true',
                        help='MOBの親プロパティ一覧を表示')
    parser.add_argument('--method-list', '-ml',
                        action='store_true',
                        help='MOBのメソッド一覧を表示')
    args = parser.parse_args()

    if(not(args.password)):
        args.password = getpass()

    return args

def multi_dimension_dict(dimension, callable_obj=int):
    """
    pythonで多次元連想配列を使う関数
    参照元: http://materia.jp/blog/20121119.html

    :type dimension: int
    :param dimension: キーの数

    :rtype: class
    :return: collections.defaultdict
    """
    nodes = defaultdict(callable_obj)
    for i in range(dimension-1):
        p = nodes.copy()
        nodes = defaultdict(lambda : defaultdict(p.default_factory))

    return nodes

def str_to_pyvmomi_class(args):
    """
    strで指定したmobをpyvmomiのclassに変換して返す

    :rtype: class
    :return: argparse.Namespace
    """
    pyvmomi_class = {}
    pyvmomi_class['Datacenter'] = vim.Datacenter
    pyvmomi_class['ClusterComputeResource'] = vim.ClusterComputeResource
    pyvmomi_class['ComputeResource'] = vim.ComputeResource
    pyvmomi_class['HostSystem'] = vim.HostSystem
    pyvmomi_class['Datastore'] = vim.Datastore
    pyvmomi_class['Folder'] = vim.Folder
    pyvmomi_class['Network'] = vim.Network
    pyvmomi_class['DistributedVirtualSwitch'] = vim.DistributedVirtualSwitch
    pyvmomi_class['DistributedVirtualPortgroup'] = vim.dvs.DistributedVirtualPortgroup
    pyvmomi_class['ResourcePool'] = vim.ResourcePool
    pyvmomi_class['VirtualMachine'] = vim.VirtualMachine

    args.mob = pyvmomi_class[args.mob]

    return args

def get_mob_info(content, mob, targets):
    """
    Management Objectを取得する。
    targetsが指定されていない場合は全mobを返す。

    :type content: vim.ServiceInstanceContent
    :param content: ServiceContent(https://goo.gl/oMtVFh)

    :type mob: Management Object
    :param mob: 取得する対象のManagement Objectを指定

    :type targets: list
    :param targets: 返すmobの名前をリストで指定

    :rtype: Management Object
    :return: 指定したManagement Object又はContainerViewを返す
    """
    r_array = []
    mob_list = content.viewManager.CreateContainerView(content.rootFolder,
                                                       [mob],
                                                       True)
    if(targets):
        for t in targets:
            for mob in mob_list.view:
                if(mob.name == t): r_array.append(mob)
    else:
        for mob in mob_list.view:
            r_array.append(mob)

    return r_array

def get_property_and_method_recursively(mob_list):
    """
    mobのプロパティ情報を再帰的に取得する。

    :rtype mob_propertys: dict
    :return mob_propertys: プロパティ情報の辞書を返す

    :rtype mob_methods: dict
    :return mob_methods: メソッド情報の辞書を返す

    :rtype fail_list: dict
    :return fail_list: 取得に失敗したプロパティ情報の辞書を返す
    """
    mob_propertys = multi_dimension_dict(2)
    mob_methods = multi_dimension_dict(2)
    fail_list = multi_dimension_dict(2)
    for mob in mob_list:
        for n in dir(mob):
            try:
                if(not(re.match(r'^_', n)) and
                (re.search(r'pyVmomi|NoneType', str(type(getattr(mob,n)))) or
                isinstance(getattr(mob,n), str))):
                    mob_propertys[mob.name][n] = getattr(mob, n)

                if(not(re.match(r'^_', n)) and isinstance(getattr(mob,n), types.FunctionType)):
                    mob_methods[mob.name][n] = n

            except:
                fail_list[mob.name][n] = 'fail'

    return mob_propertys, mob_methods, fail_list

def output_title(title):
    """
    プロパティ名やMOB名をパイプとハイフンで囲んで表示する

    :type title: str
    :param title: 名前
    """
    for num in range(0,len(title)+4): print('-', end='')
    print()
    print('| %s |' % title)
    for num in range(0,len(title)+4): print('-', end='')
    print()

def main(args):
    # SSL証明書対策
    context = None
    if hasattr(ssl, '_create_unverified_context'):
        context = ssl._create_unverified_context()

    # 接続
    si = SmartConnect(host = args.host,
                      user = args.username,
                      pwd = args.password,
                      sslContext = context)

    # 処理完了時にvCenterから切断
    atexit.register(Disconnect, si)

    # ServiceContent(Data Object)を取得
    content = si.content

    # mobリストを取得
    mob_list = get_mob_info(content, args.mob, args.target)

    # mobのpropertyとmethodを取得
    mob_propertys, mob_methods, fail_list = get_property_and_method_recursively(mob_list)

    # mobのproperty又はmethodを表示する
    if(args.method_list):
        for mob_name in sorted(mob_methods.keys(), key=str.lower):
            output_title(mob_name)
            for method_name in sorted(mob_methods[mob_name].keys()):
                print(method_name)
    else:
        for mob_name in sorted(mob_propertys.keys(), key=str.lower):
            output_title(mob_name)
            if(args.property):
                property_name = args.property
                output_title(property_name)
                if((property_name in mob_propertys[mob_name])):
                    print(mob_propertys[mob_name][property_name])
                else:
                    print("指定した %s プロパティは存在しません" % property_name)
            elif(args.property_list):
                for property_name in sorted(mob_propertys[mob_name].keys()):
                    print(property_name)
            else:
                for property_name in sorted(mob_propertys[mob_name].keys()):
                    output_title(property_name)
                    print(mob_propertys[mob_name][property_name])
    print()

    # プロパティ取得に失敗したものがあった場合に失敗したプロパティを表示
    if(fail_list):
        for mob_name in sorted(fail_list.keys(), key=str.lower):
            output_title('Fail MOB Name : %s' % mob_name)
            for property_name in sorted(fail_list[mob_name].keys()):
                print(property_name)
            print()

if __name__ == '__main__':
    args = options()
    args = str_to_pyvmomi_class(args)
    main(args)
