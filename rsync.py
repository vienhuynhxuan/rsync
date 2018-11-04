#!/usr/bin/python3
import argparse
import difflib
import os
import stat


def ParseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--times', action='append_const',
                        dest='options',
                        const='times',
                        default=[],
                        help='Add different values to list')
    parser.add_argument('-p', '--permissions', action='append_const',
                        dest='options',
                        const='permissions',
                        help='Add different values to list')
    parser.add_argument('-l', '--links', action='append_const',
                        dest='options',
                        const='symlink',
                        help='copy symlinks as symlinks')
    parser.add_argument('-H', '--hard-links', action='append_const',
                        dest='options',
                        const='hardlink',
                        help='preserce hard links')

    parser.add_argument('-r', '--recursive', action='append_const',
                        dest='options',
                        const='recursive',
                        help='recurse into directoriesman')
    parser.add_argument('-c', '--checksum', action='append_const',
                        dest='options',
                        const='checksum',
                        help='skip based on checksum, not mod-time & size')
    parser.add_argument('-u', '--update', action='append_const',
                        dest='options',
                        const='update',
                        help='skip files that are newer on the receiver')
    parser.add_argument(action='store',
                        dest='srcfile',
                        nargs='*',
                        help='Source File')
    results = parser.parse_args()
    if('times' not in results.options):
        results.options.append('times')
    if('permissions' not in results.options):
        results.options.append('permissions')
    if('symlink' not in results.options):
        results.options.append('symlink')
    if('hardlink' not in results.options):
        results.options.append('hardlink')
    if(len(results.srcfile) == 1):
        raise 'Missing Src/Dest File'
    results.destfile = results.srcfile[-1]
    results.srcfile = results.srcfile[0:-1]
    return results


def DevideBlock(string):
    result = []
    temp = ""
    for index in range(len(string)):
        temp += string[index]
        if((len(temp) == 128) or (index + 1 == len(string))):
            result.append(temp)
            temp = ""
    return result


# def CheckDiff(file1, file2):
#     with open(file1, 'r', encoding='utf-8') as src, open(file2, 'r',
#               encoding='utf-8') as dest:
#         src = src.read()
#         src = DevideBlock(src)
#         dest = dest.read()
#         dest = DevideBlock(dest)
#         diff = list(difflib.ndiff(src, dest))
#         block = []
#         result = []
#         for index in range(len(diff)):
#             block.append(diff[index])
#             continue
#             block.append(diff[index])
#             continue
#             if()
#         return (list(diff))


def SetTimes(srcFile, destFile):
    info = os.stat(srcFile)
    os.utime(destFile, (info.st_atime, info.st_mtime))


def SetPermissions(srcFile, destFile):
    permissions_srcFile = (os.stat(srcFile).st_mode)
    os.chmod(destFile, permissions_srcFile)


def KeepSymlink(srcFile, destFile):
    if os.path.islink(srcFile):
        os.unlink(destFile)
        path = os.readlink(srcFile)
        os.symlink(path, destFile)
        return 1
    return 0


def KeepHardlink(srcFile, destFile):
    if os.stat(srcFile).st_nlink != 1:
        os.unlink(destFile)
        os.link(srcFile, destFile)
        return 1
    return 0


def CopySimple(srcFile, destFile):
    check = 0
    check += KeepSymlink(srcFile, destFile)
    check += KeepHardlink(srcFile, destFile)
    if(check == 0):
        os.chmod(destFile, stat.S_IWUSR)
        srcFileOpen = open(srcFile, 'r')
        srcData = srcFileOpen.read()
        srcFileOpen.close()
        destFileOpen = open(destFile, 'w')
        destFileOpen.write(srcData)
        srcFileOpen.close()
    return True


def makeFileOrDerectory(args):
    if (os.path.exists(args.destfile) is False):
        if(len(args.srcfile) == 1 and os.path.isfile(args.srcfile[0]) is True):
            with open(args.destfile, 'w'):
                pass
        else:
            if('recursive' in args.options):
                os.mkdir(args.destfile)


def scanDirectory(dir, lst):
    listInDir = os.scandir(dir)
    for element in listInDir:
        nameElement = element.path
        if(os.path.isdir(nameElement) is False):
            lst.append(nameElement)
        else:
            scanDirectory(nameElement, lst)
    return lst


def rsyncFileToDirectory(file, dir, args):
    basenameFile = os.path.basename(file)
    lst = []
    listFile = scanDirectory(dir, lst)
    destPath = ""
    for path in listFile:
        if(basenameFile == os.path.basename(path)):
            destPath = path
            break
    if destPath == "":
        with open(dir + "/" + basenameFile, 'w'):
            pass
            destPath = dir + "/" + basenameFile
    return rsyncToFile(file, destPath, args)


def rsyncToFile(src, dest, args):
    if(len(args.srcfile) > 1):
        print('ERROR: destination must be a directory where more src file')
    else:
        if(os.path.exists(src) is False):
            print('rsync: link_stat "' + os.path.abspath(src) +
                  '" ' + 'failed: No such file or directory (2)')
            return
        if((os.stat(src).st_mode & stat.S_IRUSR) == 0):
            if(os.path.islink(src) is False):
                print('rsync: send_files failed to open "' +
                      os.path.abspath(src) + '": Permission denied (13)')
                return
        if (os.path.exists(dest) is False):
            with open(dest, 'w'):
                pass
        if('update' in args.options):
            if(os.stat(args.destfile).st_mtime
               > os.stat(args.srcfile[0]).st_mtime):
                return
        elif(os.stat(dest).st_mtime ==
             os.stat(src).st_mtime
             and os.stat(dest).st_size ==
             os.stat(src).st_size):
            if('permissions' in args.options):
                SetPermissions(src, dest)
            return
        else:
            check = CopySimple(src, dest)
            if(check is True):
                if('times' in args.options):
                    SetTimes(src, dest)
                if('permissions' in args.options):
                    SetPermissions(src, dest)
    return


# def rsyncDirectoryToDirectory(srcDir, destDir, args):
#

def main():
    args = ParseArguments()
    makeFileOrDerectory(args)
    if(os.path.isdir(args.destfile) is False):
        rsyncToFile(args.srcfile[0], args.destfile, args)
    else:
        for ele in args.srcfile:
            if(os.path.isfile(ele) is True):
                rsyncFileToDirectory(args.srcfile[0], args.destfile, args)


main()


# else:
#     if('recursive' in args.options):
#         print('ERROR: cannot overwrite non-directory')
#     else:
#         print('skipping directory ' + args.srcfile[0])
#     return
