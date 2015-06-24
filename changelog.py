
from __future__ import print_function
import fcntl
import re
import os
import select
import sys
import subprocess
import json
import smtplib
from email.mime.text import MIMEText

from color import Coloring
from command import Command
from git_command import GitCommand

class ChangelogColoring(Coloring):
   def __init__(self, config):
     Coloring.__init__(self, config, 'changelog')
     self.project = self.printer('project', attr='bold')


class Changelog(Command):
  subscribersList = {}
  common = False
  pager = False
  helpSummary = "Create a change log for each project"
  helpUsage = """
%prog [<options>] [--revisions=<revision range>] [<project>...]
"""
  helpDescription = """
Create a html changelog for each project and send an email to subscribers list

Subscribers list is a json file containing a list of projects for each subscriber

"username@domain.com" [ projects list ]

For exmaple :
{
	"user1@domain.com" : [
		"bootable/recovery",
		"docs/source.android.com"
	],
	"user2@domain.com" : [ "all" ]
}


"""

  def _Options(self, p):
    p.add_option('-r', '--regex',
                 dest='regex', action='store_true',
                 help="Execute the command only on projects matching regex or wildcard expression")
    g = p.add_option_group('Output')
    g.add_option('-v', '--verbose',
                 dest='verbose', action='store_true',
                 help='Show command error messages')
    #g.add_option('-f', '--format',
    #             dest='format', default='--oneline',
    #             help='Pretty format for git log command')
    g.add_option('--revisions',
                 dest='revisions', default='HEAD',
                 help='Revisions range')
    g.add_option('-l', '--list',
                 dest='subscribers', default=None,
                 help='A file holding the subscribers list in JSON format')

  def _ParseSubscribersList(self, filename):
    with open(filename, "r") as f:
      json_str = f.read()

    subscribers = json.loads(json_str)
    for user in subscribers:
      for proj in subscribers[user]:
        if proj not in self.subscribersList:
          self.subscribersList[proj] = []
        self.subscribersList[proj].append(user)

    out = ChangelogColoring(self.manifest.globalConfig)
   

  def _SendEmails(self, emails):

    out = ChangelogColoring(self.manifest.globalConfig)
    out.redirect(sys.stdout)
    _from = 'my@self.com'
    ret = 0

    for user in emails:
      _to = user 
      out.printer()("Sending email to %s ... ", _to)
      msg = MIMEText(emails[user], 'html')
      msg['Subject'] = 'Android changes for branch master'
      msg['From'] = _from
      msg['To'] = _to
      s = smtplib.SMTP("smtp.domain.com")
      rc = s.sendmail(_from, _to, msg.as_string())
      s.quit()
      if len(rc.keys()) == 0:
        out.printer()("OK\n")
      else:
        out.printer()("FAILED\n")
      ret |= len(rc.keys())
 
    return ret


  def WantPager(self, opt):
    return self.pager

  def Execute(self, opt, args):

    rc = 0
    out = ChangelogColoring(self.manifest.manifestProject.config)
    out.redirect(sys.stdout)

    emails = {}

    if not opt.regex:
      projects = self.GetProjects(args)
    else:
      projects = self.FindProjects(args)

    if opt.subscribers is not None:
      self._ParseSubscribersList(opt.subscribers)
    else:
      self.pager = True

    for project in projects:
      log_format = '--pretty=format:<li><a href="https://android.googlesource.com/' + project.name + '/+/%h">%h : </a>%s</li>'
      cmd_args = ['log', '--abbrev-commit', '--no-merges', log_format, opt.revisions]
      p = GitCommand(project,
                     cmd_args,
                     bare = False,
                     capture_stdout = True,
                     capture_stderr = True)

      if p.Wait() != 0:
        out.write("%s", p.stderr)
        out.nl()
        continue

      if len(p.stdout) != 0:
        proj_header = "<h2>Project: <a href='https://android.googlesource.com/%s'>%s</a></h2>" % (project.name, project.relpath)
        out.project(proj_header)
        out.nl()
        out.write("%s", p.stdout)
        out.nl()
        out.flush()

        user_list = []
        if project.relpath in self.subscribersList:
            user_list += self.subscribersList[project.relpath]
        if 'all' in self.subscribersList:
            user_list += self.subscribersList['all']

        for user in user_list:
            if user not in emails:
                emails[user] = ""
            emails[user] += proj_header + '</br>\n' + p.stdout + '</br>\n'

	
    rc = self._SendEmails(emails)
    sys.exit(rc)
