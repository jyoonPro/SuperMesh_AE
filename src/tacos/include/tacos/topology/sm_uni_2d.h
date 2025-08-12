/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#pragma once

#include <tacos/topology/topology.h>

namespace tacos {

class SM_Uni_2D final : public Topology {
  public:
    SM_Uni_2D(int width, int height, Latency latency, Bandwidth bandwidth) noexcept;

  private:
    int width;
    int height;
};

}  // namespace tacos
