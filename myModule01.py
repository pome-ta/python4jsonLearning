import re
from enum import Enum, auto
from typing import Optional


class TokenType(Enum):
  NUMBER = auto()  # 数値
  STRING = auto()  # 文字列
  BOOLEAN = auto()  # true or false
  NULL = auto()  # null

  L_BRACKET = auto()  # [
  R_BRACKET = auto()  # ]
  L_BRACE = auto()  # {
  R_BRACE = auto()  # }
  COLON = auto()  # :
  COMMA = auto()  # ,


class Token:
  def __init__(self, token_type: TokenType, value: str=None):
    self.token_type: TokenType = token_type
    self.value: str = value
    self.obj_key: bool = False
    self.nest: Optional[int] = None
    self.indent: Optional[int] = None

  def __str__(self):
    return str(self.value)


# xxx: 無駄？
def _get_symbol_dict(value: str=None) -> dict:
  return {
    '[': Token(TokenType.L_BRACKET, value),
    ']': Token(TokenType.R_BRACKET, value),
    '{': Token(TokenType.L_BRACE, value),
    '}': Token(TokenType.R_BRACE, value),
    ':': Token(TokenType.COLON, value),
    ',': Token(TokenType.COMMA, value),
  }


bools2null_dict = {
  't': 'true',
  'f': 'false',
  'n': 'null',
}


def _get_strings_step(tail_list: list) -> tuple:
  quotation_flag = False
  for n, string in enumerate(tail_list):
    if string == '"':
      if n and tail_list[n - 1] == '\\':
        continue
      if quotation_flag:
        break
      quotation_flag = True
  str_list = tail_list[:n + 1]
  str_value = ''.join(str_list[1:n])  # xxx: エスケープやら文字エンコードなど
  return Token(TokenType.STRING, str_value), len(str_list)


def _get_numbers_step(tail_list: list) -> tuple:
  end = [',', '}', ']', '\n']  # xxx: `10,000` みたいな表現できない
  for n, number in enumerate(tail_list):
    if number in end:
      break
  num_value = ''.join(tail_list[:n])
  return Token(TokenType.NUMBER, num_value), len(num_value)


def _get_bools2null_step(value_list: list) -> tuple:
  bool_null = ''.join(value_list)
  if bool_null == bools2null_dict[value_list[0]]:
    # xxx 長すぎー？
    tkn = Token(TokenType.NULL, bool_null) if bool_null == 'null' else Token(
      TokenType.BOOLEAN, bool_null)

  else:  # xxx: エラー処理
    raise Exception(f'bool or null typeError: {bool_null}')
  return tkn, len(bool_null)


def get_tokens(strs: str) -> list:
  char_list = list(strs)
  length = char_list.__len__()
  tokens = []

  flag_symbols = _get_symbol_dict().keys()
  flag_bool2null = bools2null_dict.keys()
  flag_numbers = [
    *(lambda: [str(n) for n in range(10)])(), '.', '-', 'e', 'E'
  ]  # xxx: `e`, `E` は不要？

  index = 0
  for _ in range(length):
    if index >= length:
      break
    char = char_list[index]

    if char.isspace():
      index += 1
      continue  # 空白は早々に棄却

    if char in flag_symbols:
      tkn = _get_symbol_dict(char)[char]
      add_index = 1
    elif char in flag_bool2null:
      tkn, add_index = _get_bools2null_step(
        char_list[index:index + 5 if char == 'f' else index + 4])
    elif char == '"':
      tkn, add_index = _get_strings_step(char_list[index:])
    elif char in flag_numbers:
      tkn, add_index = _get_numbers_step(char_list[index:])

    else:  # xxx: エラー処理
      raise Exception(f'Token error: {char}')
    index += add_index
    tokens.append(tkn)
  return tokens


def _setup_nest(tkn: Token, nest: int) -> int:
  if tkn.token_type in [TokenType.L_BRACE, TokenType.L_BRACKET]:
    tkn.nest = nest
    nest += 1
  if tkn.token_type in [TokenType.R_BRACE, TokenType.R_BRACKET]:
    nest -= 1
    tkn.nest = nest
  return nest


def _setup_objkey(f_tkn: Token, s_tkn: Token) -> None:
  if s_tkn and s_tkn.token_type == TokenType.COLON:
    f_tkn.obj_key = True


def _set_attributes(tokens) -> None:
  length = tokens.__len__()

  nest_num = 1  # xxx `if` 処理の`Falsy(0)` 回避のため
  for index in range(length):
    now_tkn = tokens[index]
    nest_num = _setup_nest(now_tkn, nest_num)
    next_tkn = tokens[index + 1] if index + 1 < length else None
    _setup_objkey(now_tkn, next_tkn)

  if nest_num != 1:  # xxx: エラー処理
    raise Exception('nest error: nest panic')


def _get_index2indent_dict(tokens: list) -> list:
  index_indent_list = []
  for index, tkn in enumerate(tokens):
    if tkn.nest:
      index_indent_list.append({'index': index, 'indent': tkn.nest})
  return index_indent_list


def _get_nest2indent_list(tokens: list) -> list:
  nest_indent_list = []  # xxx: `index` と、`indent` が紛らわしい？
  pool = _get_index2indent_dict(tokens)
  ref = [p for p in pool]

  length = pool.__len__()
  for open_index in range(length):
    open_nest = pool[open_index]
    if open_nest is None:
      continue
    indent_num = pool[open_index]['indent']
    pool[open_index] = None
    ref[open_index] = None

    for close_index in range(length):
      close_nest = ref[close_index]

      if close_nest and open_nest['indent'] == close_nest['indent']:
        nest_indent_list.append(
          [open_nest['index'], close_nest['index'], indent_num])
        ref[close_index] = None
        pool[close_index] = None
        break

  if len(set(pool + ref)) != 1:  # xxx: エラー処理
    raise Exception('indent error: indent panic')
  return nest_indent_list


def _set_indent(tokens: list, nests: list) -> None:
  for o, c, i in nests:
    ext_tokens = tokens[o:c + 1]
    for tkn in ext_tokens:
      tkn.indent = i


def _convert_value(tkn: Token) -> None:  # xxx: type
  if tkn.token_type == TokenType.BOOLEAN:
    value = True if re.search(r't', tkn.value) else False
  elif tkn.token_type == TokenType.NULL:
    value = None
  elif tkn.token_type == TokenType.NUMBER:
    value = float(tkn.value) if re.search(r'[\.|e|E]',
                                          tkn.value) else int(tkn.value)
  else:
    value = str(tkn.value)
  return value


def _get_dicts(tokens: list, indent: int) -> dict:
  dic_key = None
  dic_value = None
  values = []
  dicts = {}
  colon_flag = False
  children_flag = False
  for tkn in tokens:
    if tkn.indent == indent:
      dic_key = tkn.value if tkn.obj_key else dic_key

      colon_flag = True if tkn.token_type == TokenType.COLON else colon_flag

      if tkn.token_type in [TokenType.COMMA, TokenType.R_BRACE]:
        if children_flag:
          children_flag = False
          dic_value = _get_json_obj(values, indent + 1)

        dicts.update({dic_key: dic_value})
        dic_key = None
        dic_value = None
        values = []
      if colon_flag and not (
          tkn.token_type in [TokenType.COMMA, TokenType.COLON]):
        dic_value = _convert_value(tkn)

    else:
      values.append(tkn)
      children_flag = True
  return dicts


def _get_arrays(tokens: list, indent: int) -> list:
  array_value = None
  values = []
  arrays = []
  children_flag = False
  for tkn in tokens:
    if tkn.indent == indent:
      if tkn.token_type in [TokenType.COMMA, TokenType.R_BRACKET]:
        if children_flag:
          children_flag = False
          array_value = _get_json_obj(values, indent + 1)
        arrays.append(array_value)
        array_value = None
        values = []
      if not (tkn.token_type in [TokenType.L_BRACKET, TokenType.COMMA]):
        array_value = _convert_value(tkn)
    else:
      values.append(tkn)
      children_flag = True
  return arrays


def _get_json_obj(tokens: list, indent: int=1) -> dict:
  objs = None
  # todo: 再帰呼び出し開始
  if tokens[0].token_type == TokenType.L_BRACKET:
    objs = _get_arrays(tokens, indent)
  elif tokens[0].token_type == TokenType.L_BRACE:
    objs = _get_dicts(tokens, indent)
  return objs


def parse(strs: str):
  token_list = get_tokens(strs)
  _set_attributes(token_list)
  nest_indent_list = _get_nest2indent_list(token_list)
  _set_indent(token_list, nest_indent_list)
  json_objs = _get_json_obj(token_list)
  return json_objs


if __name__ == '__main__':
  from pathlib import Path
  import json

  #json_path = Path('./data/sample02.json')
  # json_path = Path('./test-data/large-file.json')
  # json_path = Path('./test-data/quarter-file.json')
  json_path = Path('./data/sample01.json')
  json_str = json_path.read_text(encoding='utf-8')
  json_main = parse(json_str)
  '''
  json_load = json.loads(json_str)
  with json_path.open(mode='r', encoding='utf_8') as f:
    json_open = json.load(f)
  print(json_load == json_open)
  '''

