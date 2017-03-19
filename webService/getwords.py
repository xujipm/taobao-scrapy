# encoding : utf-8
# author : xujipm

import tornado.ioloop
import tornado.web
from application import GetWords

import tornado.autoreload
import tornado.options
from tornado.options import define, options

settings = {'debug': True}
define("debug", default=True, help="Debug Mode", type=bool)
define("port", default=10000, help="run on the given port.", type=int)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        iid = self.get_argument("iid", "")
        callback = self.get_argument("callback", "")
        self.write('Hallo  ' + iid + "  " + callback)


# application = tornado.web.Application([
#     (r"/", MainHandler),
#     (r"/getwords.py", GetWords),
# ])

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/getwords.py", GetWords),
], **settings)


if __name__ == "__main__":
    options.parse_command_line()
    application.listen(10000)
    tornado.ioloop.IOLoop.instance().start()
