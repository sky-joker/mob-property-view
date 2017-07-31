#!/usr/bin/env python3
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
import atexit
import argparse
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
                                     description='Management Objectのプロパティ内容を表示します')
    parser.add_argument('--host', '-vc',
                        type=str, required=True,
                        help='vCenterのIP又はホスト名')
    parser.add_argument('--username', '-u',
                        type=str, default='administrator@vsphere.local',
                        help='vCenterのログインユーザー名(default:administrator@vsphere.local)')
    parser.add_argument('--password', '-p',
                        type=str, required=True,
                        help='vCenterのログインユーザーパスワード')
    parser.add_argument('--mob',
                        type=str, required=True,
                        choices=['Datacenter', 'Datastore', 'Folder', 'Network',
                        'ResourcePool', 'VirtualMachine'],
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
    args = parser.parse_args()

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
    pyvmomi_class['Datastore'] = vim.Datastore
    pyvmomi_class['Folder'] = vim.Folder
    pyvmomi_class['Network'] = vim.Network
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

def get_property_recursively(mob_list):
    """
    mobのプロパティ情報を再帰的に取得する。

    :rtype mob_propertys: dict
    :return mob_propertys: プロパティ情報の辞書を返す

    :rtype fail_list: dict
    :return fail_list: 取得に失敗したプロパティ情報の辞書を返す
    """
    mob_propertys = multi_dimension_dict(2)
    fail_list = multi_dimension_dict(2)
    for mob in mob_list:
        for n in dir(mob):
            try:
                mob_propertys[mob.name][n] = getattr(mob, n)
            except:
                fail_list[mob.name][n] = 'fail'

    return mob_propertys, fail_list

def output_property_title(property_name):
    """
    プロパティ名やMOB名を#で囲んで表示する

    :type property_name: str
    :param property_name: プロパティ名
    """
    for num in range(0,len(property_name)+4): print('-', end='')
    print()
    print('| %s |' % property_name)
    for num in range(0,len(property_name)+4): print('-', end='')
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

    # mobのpropertyを表示
    mob_propertys, fail_list = get_property_recursively(mob_list)
    for mob_name in mob_propertys.keys():
        output_property_title(mob_name)
        if(args.property):
            property_name = args.property
            output_property_title(property_name)
            if((property_name in mob_propertys[mob_name])):
                print(mob_propertys[mob_name][property_name])
            else:
                print("指定した %s プロパティは存在しません" % property_name)
        elif(args.property_list):
            for property_name in sorted(mob_propertys[mob_name].keys()):
                print(property_name)
        else:
            for property_name in sorted(mob_propertys[mob_name].keys()):
                output_property_title(property_name)
                print(mob_propertys[mob_name][property_name])
        print()

    # プロパティ取得に失敗したものがあった場合に失敗したプロパティを表示
    if(fail_list):
        for mob_name in fail_list.keys():
            output_property_title('Fail MOB Name : %s' % mob_name)
            for property_name in fail_list[mob_name].keys():
                print(property_name)
            print()

if __name__ == '__main__':
    args = options()
    args = str_to_pyvmomi_class(args)
    main(args)